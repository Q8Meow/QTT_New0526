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
    PROCESS_ROOT_ENV,
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
    _command_requires_process_retention_v1,
    _command_projection_v1,
    _local_unlinked_path,
    _scan_raise_errors,
    validate_complete_run_evidence,
    validate_published_completion_receipt,
    write_run_provenance,
)

MAX_BASETEMP_TEXT_LENGTH = 160
MAX_NESTED_EVIDENCE_COLLISIONS = 10_000
_STANDALONE_SUPERVISION = None


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


def _split_pytest_options_v1(pytest_args: Sequence[str]):
    if isinstance(pytest_args, (str, bytes)) or any(type(arg) is not str for arg in pytest_args):
        raise ValueError("pytest arguments must be exact strings")
    args = list(pytest_args)
    marker = args.index("--") if "--" in args else len(args)
    prefix, literals = args[:marker], args[marker:]
    retained = []
    selected = None
    index = 0
    while index < len(prefix):
        arg = prefix[index]
        if arg == "--basetemp" or arg.startswith("--basetemp="):
            if selected is not None:
                raise ValueError("duplicate pytest basetemp")
            if arg == "--basetemp":
                index += 1
                if index == len(prefix):
                    raise ValueError("missing pytest basetemp value")
                selected = prefix[index]
            else:
                selected = arg.split("=", 1)[1]
            if not selected or selected.startswith("-"):
                raise ValueError("invalid pytest basetemp value")
        else:
            retained.append(arg)
        index += 1
    return retained, literals, selected


def find_explicit_basetemp(pytest_args: Sequence[str]) -> str | None:
    return _split_pytest_options_v1(pytest_args)[2]


def _bind_canonical_pytest_invocation_v1(
    pytest_args: Sequence[str], *, repository_root: pathlib.Path,
    python_executable: str, run_root: pathlib.Path, environment,
):
    """Project an already admitted run; this creates no execution authority."""
    from tools.validation_reliability import _local_unlinked_path

    prefix, literals, explicit = _split_pytest_options_v1(pytest_args)
    for arg in prefix:
        if (arg.startswith("@") or arg in {"--noconftest", "--debug"}
                or any(arg == control or arg.startswith(control + "=") for control in (
                    "--rootdir", "--confcutdir", "--override-ini", "--inifile",
                    "--junitxml", "--junit-xml", "--log-file", "--debug"))
                or any(arg.startswith(control) for control in ("-c", "-o", "-p"))):
            raise ValueError("competing canonical pytest control")
    root = repository_root.resolve(strict=True)
    process_root = run_root.resolve(strict=True)
    basetemp = process_root / "p"
    cache = process_root / "pytest-cache"
    if (not root.is_dir() or not process_root.is_dir()
            or any(root == path or root.is_relative_to(path) for path in (basetemp, cache))):
        raise ValueError("pytest owned paths conflict with the repository")
    for path in (repository_root, run_root, basetemp, cache):
        _local_unlinked_path(path)
        if path.exists() and not path.is_dir():
            raise ValueError("pytest owned directory changed kind")
    if explicit is not None and explicit != str(basetemp):
        raise ValueError("pytest basetemp differs from exact admitted root")
    if type(python_executable) is not str or not python_executable:
        raise ValueError("missing admitted Python executable")
    child = {}
    removed = []
    seen = set()
    for key, value in environment.items():
        if (type(key) is not str or type(value) is not str or not key
                or "=" in key or "\0" in key or "\0" in value or key.upper() in seen):
            raise ValueError("invalid or case-colliding pytest environment")
        seen.add(key.upper())
        if key.upper().startswith("PYTEST_"):
            removed.append(key)
        elif key.upper() != "PYTHONDONTWRITEBYTECODE":
            child[key] = value
    controls = (("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1"), ("PYTHONDONTWRITEBYTECODE", "1"))
    child.update(controls)
    command = [python_executable, "-B", "-m", "pytest", "-c", str(root / "pytest.ini"),
               "-o", "addopts=", "-o", "cache_dir=" + str(cache),
               "--rootdir=" + str(root), "--confcutdir=" + str(root),
               *prefix, "--basetemp", str(basetemp), *literals]
    metadata = {"registered_argv": (python_executable, "-m", "pytest", *pytest_args),
                "removed_environment_keys": tuple(removed), "fixed_environment_controls": controls}
    return PytestInvocation(command, str(basetemp), explicit is None), child, metadata


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
        marker = forwarded_args.index("--") if "--" in forwarded_args else len(forwarded_args)
        forwarded_args[marker:marker] = ["--basetemp", str(selected_basetemp)]
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



_RP5A_PYTEST_BOOTSTRAP_V1 = (
    "from tools.run_pytest_fresh_basetemp import _rp5a_pytest_main_v1; "
    "raise SystemExit(_rp5a_pytest_main_v1())"
)


def _rp5a_forward_pytest_input_v1(bound, invocation, original_argv, environment):
    import time
    from tools.validation_reliability import (
        _ScanLaunchIdentity, _ScanLaunchInput, _scan_launch_payload, _scan_launch_measure,
    )
    attestation, scanner, reader, basis, fence, inherited = bound
    if scanner is not None or inherited is not None:
        raise ValueError("the fixed pytest wrapper requires direct reader-only custody")
    lowered = {key.upper(): value for key, value in environment.items()}
    parent = _ScanLaunchIdentity(attestation.run_id, lowered["QTT_SCAN_PHASE"], reader.command_index,
        int(lowered["QTT_SCAN_COMMAND_COUNT"]), tuple(original_argv), str(REPO_ROOT))
    command = (sys.executable, "-B", "-c", _RP5A_PYTEST_BOOTSTRAP_V1,
               str(len(parent.argv)), *parent.argv, *invocation.command[4:])
    identity = _ScanLaunchIdentity(attestation.run_id, "nested-pytest", 1, 1, command, str(REPO_ROOT))
    payload = _scan_launch_payload(identity, fence.rows, limits=fence.limits,
        candidate_read_bytes=fence.remaining, rp5a_read_basis=basis, parent_identity=parent)
    extent_bound = _scan_launch_measure(payload, limits=fence.limits) + 4
    one_check = sum(len(row.content) + sum(len(name.encode("utf-8")) for name in row.children)
                    for row in fence.rows)
    # Each native write/read can make one-byte progress: one write plus three
    # complete comparisons, each at most extent_bound iterations. The three
    # comparisons each have two endpoint checks; enter/claim/final add three.
    forwarding_reads = (4 * extent_bound + 9) * one_check
    child_reads = fence.remaining - forwarding_reads
    if child_reads <= 0 or reader.scratch_bytes < extent_bound + basis.stdout_bytes_per_call + reader.stderr_bytes_per_call:
        raise ValueError("original reader allocation cannot cover simultaneous narrowed forwarding")
    reader_root = pathlib.Path(reader.scratch_root)
    _local_unlinked_path(reader_root)
    if not reader_root.is_dir() or any(reader_root.iterdir()):
        raise ValueError("original reader allocation is not empty")
    # Two fixed child directories remain under the original run cleanup owner.
    # The input descriptor and bounded native capture must never occupy one root.
    input_root = reader_root / "pytest-input"
    capture_root = reader_root / "pytest-reads"
    input_root.mkdir()
    capture_root.mkdir()
    narrowed = _ScanLaunchInput(identity, fence.rows, limits=fence.limits,
        candidate_read_bytes=child_reads, deadline_ns=fence.deadline_ns,
        scratch_root=input_root, scratch_bytes=extent_bound,
        parent_frame_reread_bytes=3 * extent_bound, check_candidate=fence,
        rp5a_read_basis=basis, parent_identity=parent)
    if narrowed.extent > extent_bound:
        raise ValueError("narrowed frame increased its measured allocation")
    # Reserve the whole child allocation once; failed work is not refunded.
    fence.remaining = forwarding_reads
    timeout = (fence.deadline_ns - time.monotonic_ns()) / 1_000_000_000
    if timeout <= 0:
        raise TimeoutError("original RP5A reader parent deadline expired")
    return command, narrowed, timeout


def _rp5a_pytest_main_v1():
    """One literal bootstrap. Data cannot choose a module, callable or plugin."""
    from dataclasses import replace
    from tools.validation_reliability import (
        _ScanLaunchIdentity, _read_rp5a_bound_launch_fd_v1, _rp5a_consumer_role_v1,
    )
    from tools.build_pr168_rp5a_legacy_semantic_audit import (
        _rp5a_reconstruct_reader_v1, _rp5a_bound_reader_v1,
    )
    import pytest
    if tuple(sys.orig_argv[:4]) != (sys.executable, "-B", "-c", _RP5A_PYTEST_BOOTSTRAP_V1):
        raise ValueError("RP5A pytest bootstrap must be the original literal child invocation")
    if len(sys.argv) < 2 or not sys.argv[1].isascii() or not sys.argv[1].isdigit() or sys.argv[1].startswith("0"):
        raise ValueError("invalid original wrapper argv extent")
    count = int(sys.argv[1])
    if count <= 0 or count > len(sys.argv) - 2:
        raise ValueError("truncated original wrapper argv")
    parent_argv = tuple(sys.argv[2:2 + count])
    if _rp5a_consumer_role_v1(parent_argv, REPO_ROOT) != "PYTEST":
        raise ValueError("nested RP5A reader is not an original selected pytest occurrence")
    offset = 1
    while offset < len(parent_argv) and parent_argv[offset] in ("-B", "-I", "-u"):
        offset += 1
    script = pathlib.Path(parent_argv[offset])
    if script != pathlib.Path("tools/run_pytest_fresh_basetemp.py") and script != REPO_ROOT / "tools/run_pytest_fresh_basetemp.py":
        raise ValueError("only the canonical wrapper may delegate to pytest")
    invocation, _, _ = _bind_canonical_pytest_invocation_v1(
        parent_argv[offset + 1:], repository_root=REPO_ROOT, python_executable=sys.executable,
        run_root=pathlib.Path(os.environ[PROCESS_ROOT_ENV]), environment=os.environ)
    pytest_arguments = tuple(sys.argv[2 + count:])
    if pytest_arguments != tuple(invocation.command[4:]):
        raise ValueError("nested pytest argv differs from the exact canonical parent transformation")
    parent = _ScanLaunchIdentity(os.environ[RUN_ID_ENV], os.environ["QTT_SCAN_PHASE"],
        int(os.environ["QTT_SCAN_COMMAND_INDEX"]), int(os.environ["QTT_SCAN_COMMAND_COUNT"]),
        parent_argv, str(REPO_ROOT))
    _, scanner, reader, basis, fence, bound_parent = _read_rp5a_bound_launch_fd_v1(
        sys.stdin.fileno(), repo_root=REPO_ROOT, environment=os.environ.copy(),
        explicit_basetemp=pathlib.Path(invocation.basetemp), original_argv=tuple(sys.orig_argv),
        expected_role="PYTEST", expected_parent_identity=parent)
    if scanner is not None or bound_parent != parent:
        raise ValueError("nested reader lost its original one-hop parent")
    # The still-open child input occupies this originally reserved portion of
    # reader scratch. Native reads receive only the remaining simultaneous allocation.
    capture_root = pathlib.Path(reader.scratch_root) / "pytest-reads"
    _local_unlinked_path(capture_root)
    if not capture_root.is_dir() or any(capture_root.iterdir()):
        raise ValueError("original nested reader capture allocation differs")
    narrowed_reader = replace(reader, scratch_root=str(capture_root),
                              scratch_bytes=reader.scratch_bytes - fence.transport_extent)
    original = _rp5a_reconstruct_reader_v1(narrowed_reader, basis, fence)
    with _rp5a_bound_reader_v1(original):
        result = pytest.main(list(pytest_arguments))
    if result != 0:
        original.ledger.hold()
    return int(result)


def _mapper_pytest_main_v1():
    """Fixed one-hop mapper bootstrap; the data cannot select executable code."""
    from tools.validation_reliability import (
        _mapper_read_profile_for_process_v1, _mapper_bound_reads_v1,
    )
    _, binding = _mapper_read_profile_for_process_v1(REPO_ROOT,
        environment=os.environ, actual_argv=tuple(sys.orig_argv), role="CHILD")
    # Bind before pytest import/collection. Every alias calls the same io owner.
    with _mapper_bound_reads_v1(binding):
        import pytest
        return int(pytest.main(list(sys.argv[1:])))


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
    from contextlib import nullcontext
    from tools.validation_reliability import (
        _rp5a_consumer_role_v1, _read_rp5a_bound_launch_fd_v1,
        _mapper_nested_pytest_args_v1, _mapper_child_deadline_v1,
        _MAPPER_DEADLINE_ENV_KEYS,
    )
    bound = None
    mapper_binding = None
    invocation = build_pytest_invocation(forwarded)
    try:
        selected_call = (sys.executable, str(REPO_ROOT / "tools/run_pytest_fresh_basetemp.py"), *forwarded)
        if _rp5a_consumer_role_v1(selected_call, REPO_ROOT) == "PYTEST":
            bound = _read_rp5a_bound_launch_fd_v1(
                sys.stdin.fileno(), repo_root=REPO_ROOT, environment=os.environ.copy(),
                explicit_basetemp=pathlib.Path(invocation.basetemp), original_argv=tuple(sys.orig_argv),
                expected_role="PYTEST")
            attestation = bound[0]
        elif _mapper_nested_pytest_args_v1(selected_call, REPO_ROOT) is not None:
            from tools.validation_reliability import _mapper_read_profile_for_process_v1
            attestation, mapper_binding = _mapper_read_profile_for_process_v1(
                REPO_ROOT, environment=os.environ, actual_argv=tuple(sys.orig_argv), role="PARENT")
        else:
            attestation = attest_inherited_validation_run(
                REPO_ROOT,
                inherited_run_id=inherited_run_id,
                inherited_evidence_root=pathlib.Path(inherited_evidence),
                explicit_basetemp=pathlib.Path(invocation.basetemp),
            )
        invocation, child_environment, projection = _bind_canonical_pytest_invocation_v1(
            forwarded, repository_root=REPO_ROOT, python_executable=sys.executable,
            run_root=attestation.process_root, environment=os.environ,
        )
        execution_deadline_ns = None
        mapper_arguments = _mapper_nested_pytest_args_v1(selected_call, REPO_ROOT)
        if mapper_arguments is not None:
            if bound is not None or _mapper_nested_pytest_args_v1(tuple(sys.orig_argv), REPO_ROOT) != mapper_arguments:
                raise ValueError("mapper deadline lost its original ordinary invocation")
            execution_deadline_ns = _mapper_child_deadline_v1(child_environment)
            for key in _MAPPER_DEADLINE_ENV_KEYS:
                del child_environment[key]
            projection["removed_environment_keys"] += _MAPPER_DEADLINE_ENV_KEYS
        elif any(key.upper() in _MAPPER_DEADLINE_ENV_KEYS for key in child_environment):
            raise ValueError("mapper deadline controls cannot select another child")
        nested_evidence = _allocate_nested_evidence_root(
            attestation.evidence_root
        )
        print(f"pytest basetemp: {invocation.basetemp}", flush=True)
        command, original_input, timeout = invocation.command, None, None
        if mapper_binding is not None:
            if mapper_binding["basis"]["deadline_ns"] != execution_deadline_ns:
                raise ValueError("mapper read and child execution deadlines differ")
            command = list(mapper_binding["child_argv"])
            if mapper_binding['kind'] == 'MAPPER_NATIVE_READ_BINDING_V2':
                from tools.validation_reliability import _MAPPER_ACTIVATION_ENV_V1
                projection['fixed_environment_controls'] += ((_MAPPER_ACTIVATION_ENV_V1,
                    child_environment[_MAPPER_ACTIVATION_ENV_V1]),)
        if bound is not None:
            command, original_input, timeout = _rp5a_forward_pytest_input_v1(
                bound, invocation, tuple(sys.orig_argv), child_environment)
        with (nullcontext() if original_input is None else original_input), _command_projection_v1(projection):
            receipt = supervise_command(
                command,
                cwd=REPO_ROOT,
                run_id=attestation.run_id,
                phase="nested-pytest",
                command_index=1,
                evidence_root=nested_evidence,
                environment=child_environment,
                **({"launch_input": original_input, "timeout_seconds": timeout} if original_input is not None else {}),
                **({"execution_deadline_ns": execution_deadline_ns}
                   if execution_deadline_ns is not None else {}),
            )
        if bound is not None:
            bound[4]()
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
    global _STANDALONE_SUPERVISION
    if _STANDALONE_SUPERVISION is not None and _STANDALONE_SUPERVISION["pending"]:
        _print_typed_error_once(ValidationReliabilityError(
            "ENGVR_PROCESS_TERMINATION_FAILED",
            "an earlier standalone command still has unresolved process custody",
        ))
        return 1
    owned_paths = None
    probe = None
    receipt = None
    cleanup_state = "NOT_RUN"
    first_error: ValidationReliabilityError | None = None
    try:
        configured_parent = os.environ.get(PROCESS_ROOT_ENV)
        if configured_parent is not None:
            if not configured_parent or configured_parent != configured_parent.strip():
                raise ValidationReliabilityError(
                    "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
                    "configured process parent must be nonempty exact text",
                )
            _local_unlinked_path(pathlib.Path(configured_parent))
        owned_paths, probe = resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=configured_parent,
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

    supervision = {"paths": owned_paths, "phase": STANDALONE_PYTEST_HELPER_PHASE,
                   "pending": False, "receipt": None, "errors": []}
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
        invocation, child_environment, projection = _bind_canonical_pytest_invocation_v1(
            forwarded, repository_root=REPO_ROOT, python_executable=sys.executable,
            run_root=owned_paths.process_root, environment=os.environ,
        )
        write_run_provenance(
            owned_paths,
            probe,
            phase=STANDALONE_PYTEST_HELPER_PHASE,
            command_count=1,
            text_integrity_preflight_state="NOT_APPLICABLE",
        )
        print(f"pytest basetemp: {invocation.basetemp}", flush=True)
        with _command_projection_v1(projection):
            supervision["pending"] = True
            _STANDALONE_SUPERVISION = supervision
            receipt = supervise_command(
                invocation.command,
                cwd=REPO_ROOT,
                run_id=owned_paths.run_id,
                phase=STANDALONE_PYTEST_HELPER_PHASE,
                command_index=1,
                evidence_root=owned_paths.evidence_root,
                environment=child_environment,
            )
            supervision["receipt"] = receipt
        if _command_requires_process_retention_v1(receipt):
            raise ValidationReliabilityError(
                "ENGVR_PROCESS_TERMINATION_FAILED",
                "standalone command retains unresolved process custody",
            )
        if (type(receipt) is not CommandExecutionReceiptV1
                or receipt.run_id != owned_paths.run_id
                or receipt.phase != STANDALONE_PYTEST_HELPER_PHASE
                or type(receipt.command_index) is not int or receipt.command_index != 1
                or receipt.argv != tuple(invocation.command) or receipt.cwd != str(REPO_ROOT)):
            raise ValidationReliabilityError(
                "ENGVR_PROCESS_TERMINATION_FAILED",
                "standalone command receipt differs from the attempted invocation",
            )
        supervision["pending"] = False
        receipt_error = _receipt_infrastructure_error(receipt)
        if receipt_error is not None and first_error is None:
            first_error = receipt_error
    except BaseException as exc:
        supervision["errors"].append(exc)
        if receipt is not None:
            supervision["receipt"] = receipt
        errors_to_inspect = [exc]
        while errors_to_inspect:
            error = errors_to_inspect.pop()
            if isinstance(error, BaseExceptionGroup):
                errors_to_inspect.extend(reversed(error.exceptions))
            attached = getattr(error, "command_receipt", None)
            if receipt is None and type(attached) is CommandExecutionReceiptV1:
                receipt = attached
                supervision["receipt"] = attached
        first_error = _as_typed_error(
            exc,
            default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            operation="standalone pytest supervision failed",
        )
    finally:
        if (supervision["pending"] or (receipt is not None
                and _command_requires_process_retention_v1(receipt))):
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
            except BaseException as exc:
                supervision["errors"].append(exc)
                if first_error is None:
                    first_error = _as_typed_error(
                        exc,
                        default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                        operation="standalone pytest cleanup receipt failed",
                    )
        else:
            try:
                cleanup_state = cleanup_validation_run(owned_paths)
            except BaseException as exc:
                supervision["errors"].append(exc)
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
            supervision["errors"].append(exc)
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
    except BaseException as exc:
        supervision["errors"].append(exc)
        if first_error is None:
            first_error = _as_typed_error(
                exc,
                default_code="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                operation="standalone pytest completion write failed",
            )

    if any(not isinstance(error, Exception) for error in supervision["errors"]):
        _scan_raise_errors(supervision["errors"])
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
    if _STANDALONE_SUPERVISION is not None and _STANDALONE_SUPERVISION["pending"]:
        _print_typed_error_once(ValidationReliabilityError(
            "ENGVR_PROCESS_TERMINATION_FAILED",
            "an earlier standalone command still has unresolved process custody",
        ))
        return 1
    forwarded = list(sys.argv[1:] if argv is None else argv)
    try:
        _split_pytest_options_v1(forwarded)
    except (ValueError, TypeError) as exc:
        _print_typed_error_once(_as_typed_error(
            exc, default_code="ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            operation="pytest option admission failed",
        ))
        return 1
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
