#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
import pathlib
import sys
import tempfile
from typing import Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validation_reliability import (  # noqa: E402
    EVIDENCE_ROOT_ENV,
    RUN_ID_ENV,
    STANDALONE_PYTEST_HELPER_PHASE,
    CommandExecutionReceiptV1,
    ValidationCompletionReceiptV1,
    ValidationReliabilityError,
    attest_inherited_validation_run,
    atomic_write_json,
    build_command_evidence_plan,
    cleanup_validation_run,
    command_attempt_accounting,
    resolve_validation_run_paths,
    supervise_command,
    validate_complete_run_evidence,
    validate_published_completion_receipt,
    write_run_provenance,
)

MAX_BASETEMP_TEXT_LENGTH = 160
MAX_NESTED_EVIDENCE_COLLISIONS = 10_000


@dataclass(frozen=True)
class PytestInvocation:
    command: list[str]
    basetemp: str
    added_basetemp: bool


def make_fresh_basetemp(
    *, now: datetime | None = None, pid: int | None = None
) -> pathlib.Path:
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    else:
        moment = moment.astimezone(UTC)
    timestamp = moment.strftime("%Y%m%d_%H%M%S_%f")
    process_id = os.getpid() if pid is None else pid
    return (
        pathlib.Path(tempfile.gettempdir())
        / "qtt_pytest_basetemp"
        / f"pytest_{timestamp}_{process_id}"
    )


def find_explicit_basetemp(pytest_args: Sequence[str]) -> str | None:
    for index, arg in enumerate(pytest_args):
        if arg == "--basetemp":
            if index + 1 < len(pytest_args):
                return pytest_args[index + 1]
            return "<missing --basetemp value>"
        if arg.startswith("--basetemp="):
            return arg.split("=", 1)[1]
    return None


def _allocate_nested_evidence_root(
    evidence_root: pathlib.Path,
    *,
    pid: int | None = None,
) -> pathlib.Path:
    process_id = os.getpid() if pid is None else pid
    for collision_counter in range(MAX_NESTED_EVIDENCE_COLLISIONS):
        candidate = (
            evidence_root
            / f"nested-pytest-{process_id}-{collision_counter}"
        )
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        except OSError as exc:
            raise ValidationReliabilityError(
                "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                "nested pytest evidence allocation failed",
            ) from exc
        return candidate
    raise ValidationReliabilityError(
        "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        "nested pytest evidence collision budget exhausted",
    )


def build_pytest_invocation(
    pytest_args: Sequence[str], *, fresh_basetemp: pathlib.Path | None = None
) -> PytestInvocation:
    forwarded_args = list(pytest_args)
    explicit_basetemp = find_explicit_basetemp(forwarded_args)
    if explicit_basetemp is None:
        selected_basetemp = fresh_basetemp or make_fresh_basetemp()
        forwarded_args.extend(["--basetemp", str(selected_basetemp)])
        return PytestInvocation(
            command=[sys.executable, "-m", "pytest", *forwarded_args],
            basetemp=str(selected_basetemp),
            added_basetemp=True,
        )

    return PytestInvocation(
        command=[sys.executable, "-m", "pytest", *forwarded_args],
        basetemp=explicit_basetemp,
        added_basetemp=False,
    )


def _print_typed_error_once(error: ValidationReliabilityError | None) -> None:
    if error is not None:
        print(str(error), file=sys.stderr, flush=True)


def _as_typed_error(
    exc: BaseException,
    *,
    default_code: str,
    operation: str,
) -> ValidationReliabilityError:
    if isinstance(exc, ValidationReliabilityError):
        return exc
    return ValidationReliabilityError(
        default_code,
        f"{operation}: {type(exc).__name__}: {exc}",
    )


def _receipt_infrastructure_error(
    receipt: object,
) -> ValidationReliabilityError | None:
    if not isinstance(receipt, CommandExecutionReceiptV1):
        return ValidationReliabilityError(
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            "pytest supervisor returned an incomplete command receipt",
        )
    failure_class = receipt.failure_class
    if failure_class in {None, "ENGVR_NATIVE_EXIT_NONZERO"}:
        return None
    known_failures = {
        "ENGVR_PROCESS_START_FAILED",
        "ENGVR_PROCESS_TIMEOUT",
        "ENGVR_PROCESS_TERMINATION_FAILED",
        "ENGVR_REQUIRED_MARKER_MISSING",
        "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
    }
    if failure_class not in known_failures:
        return ValidationReliabilityError(
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            f"pytest supervisor returned unknown failure class: {failure_class}",
        )
    return ValidationReliabilityError(
        failure_class,
        "pytest command supervision did not reach an accepted terminal state",
    )


def _run_inherited_nested(
    forwarded: Sequence[str],
    *,
    inherited_run_id: str,
    inherited_evidence: str,
) -> int:
    explicit_basetemp = find_explicit_basetemp(forwarded)
    if explicit_basetemp is None:
        error = ValidationReliabilityError(
            "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            "inherited nested mode requires the central runner basetemp",
        )
        _print_typed_error_once(error)
        return 1
    invocation = build_pytest_invocation(forwarded)
    try:
        attestation = attest_inherited_validation_run(
            REPO_ROOT,
            inherited_run_id=inherited_run_id,
            inherited_evidence_root=pathlib.Path(inherited_evidence),
            explicit_basetemp=pathlib.Path(invocation.basetemp),
        )
        nested_evidence = _allocate_nested_evidence_root(
            attestation.evidence_root
        )
        print(f"pytest basetemp: {invocation.basetemp}", flush=True)
        receipt = supervise_command(
            invocation.command,
            cwd=REPO_ROOT,
            run_id=attestation.run_id,
            phase="nested-pytest",
            command_index=1,
            evidence_root=nested_evidence,
            environment=os.environ,
        )
    except Exception as exc:
        _print_typed_error_once(
            _as_typed_error(
                exc,
                default_code="ENGVR_PROCESS_START_FAILED",
                operation="inherited pytest supervision failed",
            )
        )
        return 1
    receipt_error = _receipt_infrastructure_error(receipt)
    _print_typed_error_once(receipt_error)
    if receipt_error is not None:
        return 1
    if receipt.native_exit_code is None:
        _print_typed_error_once(
            ValidationReliabilityError(
                "ENGVR_PROCESS_START_FAILED",
                "inherited pytest command has no native exit code",
            )
        )
        return 1
    return int(receipt.native_exit_code)


def _run_standalone_owned(forwarded: Sequence[str]) -> int:
    owned_paths = None
    probe = None
    receipt = None
    cleanup_state = "NOT_RUN"
    first_error: ValidationReliabilityError | None = None
    try:
        owned_paths, probe = resolve_validation_run_paths(
            REPO_ROOT,
            projected_relative_paths=tuple(forwarded),
        )
    except Exception as exc:
        first_error = _as_typed_error(
            exc,
            default_code="ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            operation="standalone pytest path allocation failed",
        )
        _print_typed_error_once(first_error)
        return 1

    explicit_basetemp = find_explicit_basetemp(forwarded)
    invocation = build_pytest_invocation(
        forwarded,
        fresh_basetemp=(
            None
            if explicit_basetemp is not None
            else owned_paths.pytest_basetemp_root
        ),
    )
    try:
        write_run_provenance(
            owned_paths,
            probe,
            phase=STANDALONE_PYTEST_HELPER_PHASE,
            command_count=1,
            text_integrity_preflight_state="NOT_APPLICABLE",
        )
        print(f"pytest basetemp: {invocation.basetemp}", flush=True)
        receipt = supervise_command(
            invocation.command,
            cwd=REPO_ROOT,
            run_id=owned_paths.run_id,
            phase=STANDALONE_PYTEST_HELPER_PHASE,
            command_index=1,
            evidence_root=owned_paths.evidence_root,
            environment=os.environ,
        )
        receipt_error = _receipt_infrastructure_error(receipt)
        if receipt_error is not None:
            first_error = receipt_error
    except Exception as exc:
        first_error = _as_typed_error(
            exc,
            default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            operation="standalone pytest supervision failed",
        )
    finally:
        if (
            receipt is not None
            and receipt.failure_class == "ENGVR_PROCESS_TERMINATION_FAILED"
        ):
            cleanup_state = "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
            try:
                atomic_write_json(
                    owned_paths.evidence_root / "cleanup.json",
                    {
                        "schema_version": 1,
                        "run_id": owned_paths.run_id,
                        "cleanup_target": str(owned_paths.cleanup_target),
                        "cleanup_state": cleanup_state,
                        "parent_preserved": True,
                    },
                )
            except Exception as exc:
                if first_error is None:
                    first_error = _as_typed_error(
                        exc,
                        default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                        operation="standalone pytest cleanup receipt failed",
                    )
        else:
            try:
                cleanup_state = cleanup_validation_run(owned_paths)
            except Exception as exc:
                cleanup_state = "FAIL"
                if first_error is None:
                    first_error = _as_typed_error(
                        exc,
                        default_code="ENGVR_RUN_SCOPED_CLEANUP_FAILED",
                        operation="standalone pytest cleanup failed",
                    )

    try:
        retained_receipts = () if receipt is None else (receipt,)
        expected_plan = build_command_evidence_plan(
            run_id=owned_paths.run_id,
            phase=STANDALONE_PYTEST_HELPER_PHASE,
            commands=(tuple(invocation.command),),
            cwd=REPO_ROOT,
        )
        (
            started_count,
            completed_count,
            first_failed_index,
            terminal_native_exit,
        ) = command_attempt_accounting(retained_receipts)
        receipt_failed = receipt is not None and (
            receipt.failure_class is not None or receipt.native_exit_code != 0
        )
        marker_state = (
            "NOT_RUN"
            if receipt is None
            else "PASS"
            if receipt.stdout_marker_state in {"PASS", "NOT_REQUIRED"}
            else "FAIL"
        )
        custody_error = None
        try:
            validate_complete_run_evidence(
                owned_paths,
                probe,
                phase=STANDALONE_PYTEST_HELPER_PHASE,
                command_count_planned=1,
                expected_plan=expected_plan,
                receipts=retained_receipts,
                cleanup_state=cleanup_state,
                text_integrity_preflight_state="NOT_APPLICABLE",
            )
        except ValidationReliabilityError as exc:
            custody_error = exc
            if first_error is None:
                first_error = exc
        completion = ValidationCompletionReceiptV1(
            run_id=owned_paths.run_id,
            phase=STANDALONE_PYTEST_HELPER_PHASE,
            command_count_planned=1,
            command_count_started=started_count,
            command_count_completed=completed_count,
            first_failed_command_index_or_null=(
                first_failed_index if receipt_failed else None
            ),
            terminal_native_exit_code=terminal_native_exit,
            required_marker_state=marker_state,
            process_root_cleanup_state=cleanup_state,
            evidence_root_state=(
                "PRESENT" if owned_paths.evidence_root.is_dir() else "MISSING"
            ),
            text_integrity_preflight_state="NOT_APPLICABLE",
            final_state=(
                "PASS"
                if first_error is None
                and receipt is not None
                and receipt.failure_class is None
                and receipt.native_exit_code == 0
                and cleanup_state.startswith("PASS")
                and owned_paths.evidence_root.is_dir()
                and custody_error is None
                else "FAIL"
            ),
        )
        atomic_write_json(owned_paths.evidence_root / "completion.json", completion)
        validate_published_completion_receipt(
            owned_paths.evidence_root,
            completion,
        )
    except Exception as exc:
        if first_error is None:
            first_error = _as_typed_error(
                exc,
                default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                operation="standalone pytest completion write failed",
            )

    if first_error is not None:
        _print_typed_error_once(first_error)
        return 1
    if receipt is None or receipt.native_exit_code is None:
        _print_typed_error_once(
            ValidationReliabilityError(
                "ENGVR_PROCESS_START_FAILED",
                "standalone pytest command has no native exit code",
            )
        )
        return 1
    return int(receipt.native_exit_code)


def main(argv: Sequence[str] | None = None) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    inherited_evidence = os.environ.get(EVIDENCE_ROOT_ENV, "").strip()
    inherited_run_id = os.environ.get(RUN_ID_ENV, "").strip()
    if bool(inherited_evidence) != bool(inherited_run_id):
        _print_typed_error_once(
            ValidationReliabilityError(
                "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                "inherited run ID and evidence root must be supplied together",
            )
        )
        return 1
    if inherited_evidence and inherited_run_id:
        return _run_inherited_nested(
            forwarded,
            inherited_run_id=inherited_run_id,
            inherited_evidence=inherited_evidence,
        )
    return _run_standalone_owned(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
