from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import tempfile

import pytest

from tools import run_pytest_fresh_basetemp as helper
from tools import validation_reliability as reliability


def _fixed_basetemp() -> Path:
    return (
        Path(tempfile.gettempdir())
        / "qtt_pytest_basetemp"
        / "pytest_20260508_120000_000000_1234"
    )


def _custom_basetemp() -> Path:
    return Path(tempfile.gettempdir()) / "qtt_pytest_custom"


def _new_evidence_root(parent: Path, before: set[Path]) -> Path:
    created = set(parent.glob("*.evidence")) - before
    assert len(created) == 1
    return created.pop()


def _attested_outer_run(
    repo_root: Path,
    process_parent: Path,
    run_id: str,
):
    paths, probe = reliability.resolve_validation_run_paths(
        repo_root,
        explicit_process_root=process_parent.resolve(),
        run_id=run_id,
        projected_relative_paths=("nested-pytest/command-1.stdout.bin",),
    )
    reliability.write_run_provenance(
        paths,
        probe,
        phase="outer-test-run",
        command_count=1,
        text_integrity_preflight_state="PASS",
    )
    return paths, probe


def _standalone_helper_call(
    monkeypatch,
    *,
    repo_root: Path,
    process_parent: Path,
    argv: list[str],
) -> tuple[int, Path]:
    before = set(process_parent.glob("*.evidence"))
    with monkeypatch.context() as call_patch:
        call_patch.setattr(helper, "REPO_ROOT", repo_root)
        call_patch.setenv(reliability.PROCESS_ROOT_ENV, str(process_parent))
        call_patch.delenv(reliability.RUN_ID_ENV, raising=False)
        call_patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
        exit_code = helper.main(argv)
    return exit_code, _new_evidence_root(process_parent, before)


def _command_receipt(
    command,
    kwargs,
    tmp_path: Path,
    *,
    native_exit_code: int | None,
    failure_class: str,
    start_failure_class: str | None = None,
    timeout_seconds: float | None = None,
    timeout_state: str = "NOT_CONFIGURED",
    termination_state: str = "NOT_REQUIRED",
    required_markers: tuple[str, ...] = (),
    marker_state: str = "NOT_REQUIRED",
) -> reliability.CommandExecutionReceiptV1:
    evidence_root = tmp_path / "typed-receipt-evidence"
    return reliability.CommandExecutionReceiptV1(
        schema_version=reliability.SCHEMA_VERSION,
        run_id=kwargs["run_id"],
        phase=kwargs["phase"],
        command_index=kwargs["command_index"],
        argv=tuple(command),
        cwd=str(Path(kwargs["cwd"]).resolve()),
        pid=None if start_failure_class is not None else 4242,
        platform=os.name,
        start_time_utc="2026-08-24T00:00:00Z",
        end_time_utc="2026-08-24T00:00:01Z",
        elapsed_monotonic_seconds=1.0,
        native_exit_code=native_exit_code,
        start_failure_class=start_failure_class,
        timeout_seconds_or_null=timeout_seconds,
        timeout_state=timeout_state,
        termination_state=termination_state,
        stdout_path=str((evidence_root / "command-1.stdout.bin").resolve()),
        stderr_path=str((evidence_root / "command-1.stderr.bin").resolve()),
        stdout_byte_count=0,
        stderr_byte_count=0,
        stdout_required_markers=required_markers,
        stdout_marker_state=marker_state,
        stderr_was_nonempty=False,
        failure_class=failure_class,
    )


def _assert_inherited_receipt_fail_closed_matrix(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    real_supervise_command = helper.supervise_command
    original_run_id = os.environ.get(reliability.RUN_ID_ENV)
    original_evidence_root = os.environ.get(reliability.EVIDENCE_ROOT_ENV)
    matrix = (
        (
            {"malformed": True},
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        ),
        (
            {"native_exit_code": 0, "failure_class": "UNKNOWN_FAILURE_CLASS"},
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        ),
        (
            {
                "native_exit_code": None,
                "failure_class": "ENGVR_PROCESS_START_FAILED",
                "start_failure_class": "FileNotFoundError",
            },
            "ENGVR_PROCESS_START_FAILED",
        ),
        (
            {
                "native_exit_code": 1,
                "failure_class": "ENGVR_PROCESS_TIMEOUT",
                "timeout_seconds": 1.0,
                "timeout_state": "TRIGGERED",
                "termination_state": "TERMINAL:PROVEN",
            },
            "ENGVR_PROCESS_TIMEOUT",
        ),
        (
            {
                "native_exit_code": 1,
                "failure_class": "ENGVR_PROCESS_TERMINATION_FAILED",
                "timeout_seconds": 1.0,
                "timeout_state": "TRIGGERED",
                "termination_state": "TERMINAL:UNPROVEN",
            },
            "ENGVR_PROCESS_TERMINATION_FAILED",
        ),
        (
            {
                "native_exit_code": 0,
                "failure_class": "ENGVR_REQUIRED_MARKER_MISSING",
                "required_markers": ("REQUIRED",),
                "marker_state": "MISSING:REQUIRED",
            },
            "ENGVR_REQUIRED_MARKER_MISSING",
        ),
        (
            {
                "native_exit_code": 0,
                "failure_class": "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            },
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        ),
    )
    inherited_repo = tmp_path / "inherited-failure-repo"
    inherited_repo.mkdir(exist_ok=True)
    for case_index, (specification, expected_code) in enumerate(matrix, start=1):
        outer_paths, _probe = _attested_outer_run(
            inherited_repo,
            tmp_path / f"inherited-failure-parent-{case_index}",
            f"run_inherited_failure_matrix_{case_index}",
        )
        with monkeypatch.context() as receipt_patch:
            receipt_patch.setattr(helper, "REPO_ROOT", inherited_repo)
            receipt_patch.setenv(reliability.RUN_ID_ENV, outer_paths.run_id)
            receipt_patch.setenv(
                reliability.EVIDENCE_ROOT_ENV,
                str(outer_paths.evidence_root),
            )
            if specification.get("malformed"):
                receipt = object()
            else:
                receipt = None

            def fake_supervise(command, **kwargs):
                if receipt is not None:
                    return receipt
                parameters = dict(specification)
                parameters.pop("malformed", None)
                return _command_receipt(command, kwargs, tmp_path, **parameters)

            receipt_patch.setattr(helper, "supervise_command", fake_supervise)
            result = helper.main(
                [
                    "tests/fail_closed",
                    "--basetemp",
                    str(outer_paths.pytest_basetemp_root),
                    "-q",
                ]
            )
        output = capsys.readouterr()
        assert result == 1
        assert expected_code in output.err
        assert "Traceback" not in output.err
        assert helper.supervise_command is real_supervise_command
        assert os.environ.get(reliability.RUN_ID_ENV) == original_run_id
        assert os.environ.get(reliability.EVIDENCE_ROOT_ENV) == original_evidence_root


def _assert_inherited_outer_run_attestation(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "inherited-attestation-repo"
    repo_root.mkdir()
    cases: list[tuple[str, Path, Path]] = []

    missing_root = (tmp_path / "missing-provenance-evidence").resolve()
    missing_root.mkdir()
    cases.append(("run_missing_provenance", missing_root, tmp_path.resolve()))

    wrong_id_paths, _probe = _attested_outer_run(
        repo_root,
        tmp_path / "wrong-id-parent",
        "run_attested_wrong_id",
    )
    cases.append(
        (
            "run_different_id",
            wrong_id_paths.evidence_root,
            wrong_id_paths.pytest_basetemp_root,
        )
    )

    wrong_basetemp_paths, _probe = _attested_outer_run(
        repo_root,
        tmp_path / "wrong-basetemp-parent",
        "run_attested_wrong_basetemp",
    )
    cases.append(
        (
            wrong_basetemp_paths.run_id,
            wrong_basetemp_paths.evidence_root,
            (tmp_path / "outside-declared-basetemp").resolve(),
        )
    )

    for label, field, wrong_value in (
        ("wrong-repository", "repo_root", tmp_path / "different-repo"),
        ("wrong-evidence", "evidence_root", tmp_path / "different-evidence"),
    ):
        paths, _probe = _attested_outer_run(
            repo_root,
            tmp_path / f"{label}-parent",
            f"run_attested_{label}",
        )
        run_path = paths.evidence_root / "run.json"
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        payload["paths"][field] = str(wrong_value.resolve())
        run_path.write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        cases.append((paths.run_id, paths.evidence_root, paths.pytest_basetemp_root))

    local_evidence = repo_root / "repository-local-evidence"
    local_evidence.mkdir()
    local_source_paths, _probe = _attested_outer_run(
        repo_root,
        tmp_path / "local-source-parent",
        "run_attested_repository_local",
    )
    local_payload = json.loads(
        (local_source_paths.evidence_root / "run.json").read_text(encoding="utf-8")
    )
    local_payload["paths"]["evidence_root"] = str(local_evidence.resolve())
    (local_evidence / "run.json").write_text(
        json.dumps(local_payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    cases.append(
        (
            local_source_paths.run_id,
            local_evidence,
            local_source_paths.pytest_basetemp_root,
        )
    )

    linked_source_paths, _probe = _attested_outer_run(
        repo_root,
        tmp_path / "linked-source-parent",
        "run_attested_linked_root",
    )
    linked_evidence = tmp_path / "linked-evidence-root"
    try:
        os.symlink(
            linked_source_paths.evidence_root,
            linked_evidence,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError):
        assert os.name == "nt"
    else:
        cases.append(
            (
                linked_source_paths.run_id,
                linked_evidence,
                linked_source_paths.pytest_basetemp_root,
            )
        )

    child_starts = []

    def must_not_start(*args, **kwargs):
        child_starts.append((args, kwargs))
        raise AssertionError("attestation failure launched a child")

    for run_id, evidence_root, basetemp in cases:
        before_nested = set(tmp_path.rglob("nested-pytest-*"))
        with monkeypatch.context() as attestation_patch:
            attestation_patch.setattr(helper, "REPO_ROOT", repo_root)
            attestation_patch.setattr(helper, "supervise_command", must_not_start)
            attestation_patch.setenv(reliability.RUN_ID_ENV, run_id)
            attestation_patch.setenv(
                reliability.EVIDENCE_ROOT_ENV,
                str(evidence_root),
            )
            result = helper.main(
                ["--version", "--basetemp", str(basetemp)]
            )
        output = capsys.readouterr()
        assert result == 1
        assert "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED" in output.err
        assert "Traceback" not in output.err
        assert set(tmp_path.rglob("nested-pytest-*")) == before_nested

    for only_run_id, only_evidence in (
        ("run_stale_pair", None),
        (None, str(missing_root)),
    ):
        with monkeypatch.context() as stale_patch:
            stale_patch.setattr(helper, "REPO_ROOT", repo_root)
            stale_patch.setattr(helper, "supervise_command", must_not_start)
            if only_run_id is None:
                stale_patch.delenv(reliability.RUN_ID_ENV, raising=False)
            else:
                stale_patch.setenv(reliability.RUN_ID_ENV, only_run_id)
            if only_evidence is None:
                stale_patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
            else:
                stale_patch.setenv(reliability.EVIDENCE_ROOT_ENV, only_evidence)
            result = helper.main(["--version", "--basetemp", str(tmp_path)])
        output = capsys.readouterr()
        assert result == 1
        assert "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED" in output.err
        assert "Traceback" not in output.err
    assert child_starts == []


def _assert_standalone_helper_receipt_matrix(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    assert helper.supervise_command is reliability.supervise_command
    assert helper.validate_complete_run_evidence is (
        reliability.validate_complete_run_evidence
    )
    assert helper.validate_published_completion_receipt is (
        reliability.validate_published_completion_receipt
    )
    matrix_root = tmp_path / "helper-terminal-custody"
    repo_root = matrix_root / "repo"
    repo_root.mkdir(parents=True)

    success_parent = matrix_root / "success-process-parent"
    custody_calls = []
    completion_validation_calls = []
    real_custody_validator = helper.validate_complete_run_evidence
    real_completion_validator = helper.validate_published_completion_receipt

    def track_custody(*args, **kwargs):
        custody_calls.append((args, kwargs))
        return real_custody_validator(*args, **kwargs)

    def track_completion(*args, **kwargs):
        completion_validation_calls.append((args, kwargs))
        return real_completion_validator(*args, **kwargs)

    with monkeypatch.context() as custody_patch:
        custody_patch.setattr(helper, "validate_complete_run_evidence", track_custody)
        custody_patch.setattr(
            helper,
            "validate_published_completion_receipt",
            track_completion,
        )
        success_exit, success_evidence = _standalone_helper_call(
            monkeypatch,
            repo_root=repo_root,
            process_parent=success_parent,
            argv=["--version"],
        )
    assert success_exit == 0
    assert len(custody_calls) == 1
    assert len(completion_validation_calls) == 1
    success_output = capsys.readouterr()
    assert "pytest basetemp:" in success_output.out
    assert "Traceback" not in success_output.err
    expected_files = {
        "cleanup.json",
        "command-1.json",
        "command-1.stderr.bin",
        "command-1.stdout.bin",
        "completion.json",
        "run.json",
    }
    actual_files = {
        path.relative_to(success_evidence).as_posix()
        for path in success_evidence.rglob("*")
        if path.is_file()
    }
    assert actual_files == expected_files
    run_payload = json.loads(
        (success_evidence / "run.json").read_text(encoding="utf-8")
    )
    command_payload = json.loads(
        (success_evidence / "command-1.json").read_text(encoding="utf-8")
    )
    cleanup_payload = json.loads(
        (success_evidence / "cleanup.json").read_text(encoding="utf-8")
    )
    completion_payload = json.loads(
        (success_evidence / "completion.json").read_text(encoding="utf-8")
    )
    assert run_payload["phase"] == reliability.STANDALONE_PYTEST_HELPER_PHASE
    assert run_payload["command_count"] == 1
    assert run_payload["text_integrity_preflight_state"] == "NOT_APPLICABLE"
    assert command_payload["command_index"] == 1
    assert command_payload["native_exit_code"] == 0
    assert reliability.command_receipt_file_indexes(success_evidence) == (1,)
    assert cleanup_payload["cleanup_state"].startswith("PASS")
    assert not Path(cleanup_payload["cleanup_target"]).exists()
    assert completion_payload["command_count_planned"] == 1
    assert completion_payload["command_count_started"] == 1
    assert completion_payload["command_count_completed"] == 1
    assert completion_payload["terminal_native_exit_code"] == 0
    assert completion_payload["evidence_root_state"] == "PRESENT"
    assert completion_payload["text_integrity_preflight_state"] == (
        "NOT_APPLICABLE"
    )
    assert completion_payload["final_state"] == "PASS"
    assert (success_evidence / "run.json").stat().st_mtime_ns <= (
        success_evidence / "command-1.json"
    ).stat().st_mtime_ns
    assert (success_evidence / "cleanup.json").stat().st_mtime_ns <= (
        success_evidence / "completion.json"
    ).stat().st_mtime_ns

    nonzero_parent = matrix_root / "nonzero-process-parent"
    nonzero_exit, nonzero_evidence = _standalone_helper_call(
        monkeypatch,
        repo_root=repo_root,
        process_parent=nonzero_parent,
        argv=["--definitely-not-a-real-pytest-option"],
    )
    assert nonzero_exit != 0
    capsys.readouterr()
    nonzero_completion = json.loads(
        (nonzero_evidence / "completion.json").read_text(encoding="utf-8")
    )
    nonzero_cleanup = json.loads(
        (nonzero_evidence / "cleanup.json").read_text(encoding="utf-8")
    )
    assert nonzero_completion["terminal_native_exit_code"] == nonzero_exit
    assert nonzero_completion["first_failed_command_index_or_null"] == 1
    assert nonzero_completion["final_state"] == "FAIL"
    assert nonzero_cleanup["cleanup_state"].startswith("PASS")

    prestart_parent = matrix_root / "prestart-process-parent"
    prestart_exit, prestart_evidence = _standalone_helper_call(
        monkeypatch,
        repo_root=repo_root,
        process_parent=prestart_parent,
        argv=["embedded\0nul"],
    )
    assert prestart_exit != 0
    prestart_output = capsys.readouterr()
    assert "ENGVR_PROCESS_START_FAILED" in prestart_output.err
    assert "Traceback" not in prestart_output.err
    prestart_command = json.loads(
        (prestart_evidence / "command-1.json").read_text(encoding="utf-8")
    )
    prestart_completion = json.loads(
        (prestart_evidence / "completion.json").read_text(encoding="utf-8")
    )
    assert prestart_command["pid"] is None
    assert prestart_command["native_exit_code"] is None
    assert prestart_command["failure_class"] == "ENGVR_PROCESS_START_FAILED"
    assert prestart_completion["command_count_started"] == 0
    assert prestart_completion["command_count_completed"] == 0
    assert prestart_completion["first_failed_command_index_or_null"] == 1
    assert prestart_completion["final_state"] == "FAIL"
    assert not list(prestart_evidence.glob(".command-*.reserve"))
    assert not list(prestart_evidence.glob(".*.tmp"))

    cleanup_parent = matrix_root / "cleanup-failure-process-parent"
    real_rmtree = reliability.shutil.rmtree
    before_cleanup_evidence = set(cleanup_parent.glob("*.evidence"))
    with monkeypatch.context() as cleanup_patch:
        cleanup_patch.setattr(helper, "REPO_ROOT", repo_root)
        cleanup_patch.setenv(reliability.PROCESS_ROOT_ENV, str(cleanup_parent))
        cleanup_patch.delenv(reliability.RUN_ID_ENV, raising=False)
        cleanup_patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
        cleanup_patch.setattr(
            reliability.shutil,
            "rmtree",
            lambda _target, *, onexc: (_ for _ in ()).throw(
                PermissionError("synthetic cleanup failure")
            ),
        )
        cleanup_exit = helper.main(["--version"])
    assert cleanup_exit != 0
    cleanup_output = capsys.readouterr()
    assert "ENGVR_RUN_SCOPED_CLEANUP_FAILED" in cleanup_output.err
    assert "Traceback" not in cleanup_output.err
    cleanup_evidence = _new_evidence_root(
        cleanup_parent,
        before_cleanup_evidence,
    )
    cleanup_failure_payload = json.loads(
        (cleanup_evidence / "cleanup.json").read_text(encoding="utf-8")
    )
    cleanup_completion = json.loads(
        (cleanup_evidence / "completion.json").read_text(encoding="utf-8")
    )
    failed_root = Path(cleanup_failure_payload["cleanup_target"])
    assert failed_root.is_dir()
    assert cleanup_failure_payload["cleanup_state"].startswith("FAIL")
    assert cleanup_completion["process_root_cleanup_state"] == "FAIL"
    assert cleanup_completion["final_state"] == "FAIL"
    real_rmtree(failed_root)

    inherited_paths, _inherited_probe = _attested_outer_run(
        repo_root,
        matrix_root / "inherited-process-parent",
        "run_inherited_matrix",
    )
    inherited_evidence = inherited_paths.evidence_root
    inherited_basetemp = inherited_paths.pytest_basetemp_root
    inherited_run_before = (inherited_evidence / "run.json").read_bytes()
    collision_root = (
        inherited_evidence / f"nested-pytest-{os.getpid()}-0"
    )
    collision_root.mkdir()
    collision_sentinel = collision_root / "prior-evidence.bin"
    collision_sentinel.write_bytes(b"PRIOR_EVIDENCE")
    with monkeypatch.context() as inherited_patch:
        inherited_patch.setattr(helper, "REPO_ROOT", repo_root)
        inherited_patch.setenv(reliability.RUN_ID_ENV, inherited_paths.run_id)
        inherited_patch.setenv(
            reliability.EVIDENCE_ROOT_ENV,
            str(inherited_evidence),
        )
        inherited_exit = helper.main(
            ["--version", "--basetemp", str(inherited_basetemp)]
        )
    assert inherited_exit == 0
    inherited_output = capsys.readouterr()
    assert "Traceback" not in inherited_output.err
    assert (inherited_evidence / "run.json").read_bytes() == inherited_run_before
    assert not (inherited_evidence / "completion.json").exists()
    assert not (inherited_evidence / "cleanup.json").exists()
    nested_roots = tuple(inherited_evidence.glob("nested-pytest-*"))
    assert len(nested_roots) == 2
    assert collision_sentinel.read_bytes() == b"PRIOR_EVIDENCE"
    selected_nested_root = next(
        path for path in nested_roots if path != collision_root
    )
    assert selected_nested_root.name == f"nested-pytest-{os.getpid()}-1"
    assert {
        path.name for path in selected_nested_root.iterdir() if path.is_file()
    } == {
        "command-1.json",
        "command-1.stderr.bin",
        "command-1.stdout.bin",
    }

    with monkeypatch.context() as typed_failure_patch:
        typed_failure_patch.setattr(helper, "REPO_ROOT", repo_root)
        typed_failure_patch.delenv(reliability.RUN_ID_ENV, raising=False)
        typed_failure_patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
        typed_failure_patch.setattr(
            helper,
            "resolve_validation_run_paths",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                reliability.ValidationReliabilityError(
                    "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
                    "synthetic allocation failure",
                )
            ),
        )
        typed_exit = helper.main(["--version"])
    assert typed_exit != 0
    typed_output = capsys.readouterr()
    assert typed_output.err.count("ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE") == 1
    assert "Traceback" not in typed_output.err
    with pytest.raises(ValueError, match="terminal invariant"):
        reliability.ValidationCompletionReceiptV1(
            run_id="run_aggregate_cannot_skip_text_preflight",
            phase="all",
            command_count_planned=1,
            command_count_started=1,
            command_count_completed=1,
            first_failed_command_index_or_null=None,
            terminal_native_exit_code=0,
            required_marker_state="PASS",
            process_root_cleanup_state="PASS_REMOVED_EXACT_RUN_ROOT",
            evidence_root_state="PRESENT",
            text_integrity_preflight_state="NOT_APPLICABLE",
            final_state="PASS",
        )

    # Append isolated caller faults after the existing actual-child matrix.
    # These receipt/evidence ports are fixtures, not saved native command proof.
    from contextlib import contextmanager
    from dataclasses import replace
    for fault in ("success", "nonzero", "marker", "prestart", "terminal-publication",
                  "unproven", "exception", "group", "cancel", "system-exit", "base-group",
                  "context-exit", "publication-error", "group-publication", "report-error", "missing", "shape",
                  "bool-pid", "bool-exit", "unknown", "conflicting-proof",
                  "run", "phase", "index", "argv", "cwd"):
        parent = matrix_root / ("pending-" + fault)
        primary = reliability.ValidationReliabilityError(
            "ENGVR_PROCESS_TERMINATION_FAILED", "original unresolved supervision",
        )
        primary.owned_process = object()
        publication = OSError("original receipt publication failed")
        reporting = OSError("cleanup/completion reporting unavailable")
        raised = (ExceptionGroup("outer", [ExceptionGroup("inner", [primary])])
                  if fault in {"group", "group-publication"} else KeyboardInterrupt("original interruption")
                  if fault == "cancel" else SystemExit(17) if fault == "system-exit"
                  else BaseExceptionGroup("mixed", [KeyboardInterrupt(), primary])
                  if fault == "base-group" else primary)
        context_error = RuntimeError("original projection exit failed")
        starts, actual_receipts, deleted, writes, validations = [], [], [], [], []
        real_cleanup = helper.cleanup_validation_run
        real_write = helper.atomic_write_json

        @contextmanager
        def fail_projection_exit(_projection):
            yield
            raise context_error

        def fixture_supervise(command, **kwargs):
            starts.append((tuple(command), kwargs))
            if fault in {"exception", "group", "cancel", "system-exit", "base-group", "report-error"}:
                raise raised
            parameters = {"native_exit_code": 0, "failure_class": None}
            if fault == "nonzero":
                parameters.update(native_exit_code=7, failure_class="ENGVR_NATIVE_EXIT_NONZERO")
            elif fault == "marker":
                parameters.update(failure_class="ENGVR_REQUIRED_MARKER_MISSING",
                                  required_markers=("EXPECTED",), marker_state="MISSING:EXPECTED")
            elif fault == "prestart":
                parameters.update(native_exit_code=None, failure_class="ENGVR_PROCESS_START_FAILED",
                                  start_failure_class="FileNotFoundError")
            elif fault in {"unproven", "terminal-publication"}:
                parameters.update(failure_class="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED")
                if fault == "unproven":
                    parameters.update(termination_state="TASKKILL_T:128;TERMINAL:UNPROVEN")
            elif fault in {"publication-error", "group-publication"}:
                parameters.update(failure_class="ENGVR_PROCESS_TERMINATION_FAILED",
                                  termination_state="TASKKILL_T:128;TERMINAL:UNPROVEN")
            receipt = _command_receipt(command, kwargs, tmp_path, **parameters)
            changes = {
                "bool-pid": {"pid": True}, "bool-exit": {"native_exit_code": False},
                "unknown": {"termination_state": "UNKNOWN"},
                "conflicting-proof": {"termination_state": "TASKKILL_T:0;TERMINAL:PROVEN;UNPROVEN"},
                "run": {"run_id": "different_run"}, "phase": {"phase": "different-phase"},
                "index": {"command_index": 2}, "argv": {"argv": (*tuple(command), "--different")},
                "cwd": {"cwd": str(tmp_path)},
            }.get(fault, {})
            receipt = replace(receipt, **changes)
            if fault == "missing":
                receipt = None
            elif fault == "shape":
                receipt = {"pid": 4242, "native_exit_code": 0}
            actual_receipts.append(receipt)
            if fault in {"publication-error", "group-publication"}:
                primary.command_receipt = receipt
                if fault == "group-publication":
                    primary.__cause__ = publication
                    raise raised
                raise primary from publication
            return receipt

        def observe_cleanup(paths):
            deleted.append(paths)
            return real_cleanup(paths)

        def observe_write(path, payload):
            writes.append((path.name, payload))
            if fault == "report-error":
                raise reporting
            return real_write(path, payload)

        def observe_validation(*args, **kwargs):
            validations.append(kwargs)

        with monkeypatch.context() as fault_patch:
            fault_patch.setattr(helper, "_STANDALONE_SUPERVISION", None)
            fault_patch.setattr(helper, "REPO_ROOT", repo_root)
            fault_patch.setenv(reliability.PROCESS_ROOT_ENV, str(parent))
            fault_patch.delenv(reliability.RUN_ID_ENV, raising=False)
            fault_patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
            fault_patch.setattr(helper, "supervise_command", fixture_supervise)
            fault_patch.setattr(helper, "cleanup_validation_run", observe_cleanup)
            fault_patch.setattr(helper, "atomic_write_json", observe_write)
            fault_patch.setattr(helper, "validate_complete_run_evidence", observe_validation)
            fault_patch.setattr(helper, "validate_published_completion_receipt", lambda *args: None)
            if fault == "context-exit":
                fault_patch.setattr(helper, "_command_projection_v1", fail_projection_exit)
            if fault in {"cancel", "system-exit", "base-group"}:
                with pytest.raises(type(raised)) as caught:
                    helper.main(["--version"])
                assert caught.value is raised
            else:
                result = helper.main(["--version"])
                assert result == (0 if fault == "success" else 7 if fault == "nonzero" else 1)
            pending = helper._STANDALONE_SUPERVISION
            assert len(starts) == 1
            terminal = fault in {"success", "nonzero", "marker", "prestart", "terminal-publication"}
            if terminal:
                assert pending["pending"] is False
                assert deleted == [pending["paths"]]
                assert not pending["paths"].process_root.exists()
                assert writes[-1][1].final_state == ("PASS" if fault == "success" else "FAIL")
            else:
                assert pending["pending"] is True
                assert deleted == [] and pending["paths"].process_root.is_dir()
                assert writes[0][0] == "cleanup.json"
                assert writes[0][1]["cleanup_state"] == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
                before_retry = set(parent.iterdir())
                assert helper.main(["--version"]) == 1
                assert helper._STANDALONE_SUPERVISION is pending
                assert set(parent.iterdir()) == before_retry and len(starts) == 1
                if fault == "unproven":
                    inherited_calls = []
                    fault_patch.setenv(reliability.RUN_ID_ENV, "different_inherited_run")
                    fault_patch.setenv(reliability.EVIDENCE_ROOT_ENV, str(parent))
                    fault_patch.setattr(helper, "_run_inherited_nested",
                                        lambda *args, **kwargs: inherited_calls.append((args, kwargs)))
                    assert helper.main(["--version"]) == 1
                    assert inherited_calls == []
                    assert helper._STANDALONE_SUPERVISION is pending
            if fault in {"exception", "group", "cancel", "system-exit", "base-group", "report-error", "publication-error", "group-publication"}:
                assert pending["errors"][0] is raised
            if fault == "context-exit":
                assert pending["errors"][0] is context_error
            if fault == "report-error":
                assert any(error is reporting for error in pending["errors"])
                assert [name for name, _ in writes] == ["cleanup.json", "completion.json"]
            if actual_receipts and type(actual_receipts[0]) is reliability.CommandExecutionReceiptV1:
                assert pending["receipt"] is actual_receipts[0]
                assert len(validations) == 1
                assert len(validations[0]["receipts"]) == 1
                assert validations[0]["receipts"][0] is actual_receipts[0]
            elif fault not in {"shape", "missing"}:
                assert pending["receipt"] is None
                assert validations[0]["receipts"] == ()
            if fault in {"publication-error", "group-publication"}:
                assert primary.__cause__ is publication
                assert primary.command_receipt is actual_receipts[0]
                assert not (pending["paths"].evidence_root / "command-1.json").exists()
        capsys.readouterr()


def test_helper_builds_pytest_command_using_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(helper.sys, "executable", python_executable)

    invocation = helper.build_pytest_invocation(
        ["tests/fail_closed", "-q"],
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.command[:3] == [python_executable, "-m", "pytest"]


def test_helper_adds_basetemp_when_absent():
    pytest_args = ["tests/fail_closed", "-q"]
    basetemp = _fixed_basetemp()

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=basetemp,
    )

    assert invocation.added_basetemp is True
    assert invocation.basetemp == str(basetemp)
    assert invocation.command[3:-2] == pytest_args

    assert invocation.command[-2:] == ["--basetemp", str(basetemp)]


def test_helper_preserves_user_pytest_args(tmp_path):
    pytest_args = ["tests/fail_closed", "-q", "-k", "scanner"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.command[3:-2] == pytest_args

    # These synthetic owned paths exercise textual projection, not host qualification.
    repository = tmp_path / "canonical-repository"
    run_root = tmp_path / "canonical-run"
    repository.mkdir()
    run_root.mkdir()
    original = ["tests/fail_closed", "-q", "--", "--basetemp=literal-test-name"]
    environment = {"Path": "admitted-fixture-path", "PYTEST_ADDOPTS": "--basetemp=outside",
                   "pytest_plugins": "unadmitted_plugin", "PYTEST_DEBUG": "1", "PYTEST_CURRENT_TEST": "fixture"}
    parent = dict(environment)
    bound, child, projection = helper._bind_canonical_pytest_invocation_v1(
        original, repository_root=repository, python_executable=helper.sys.executable,
        run_root=run_root, environment=environment)
    assert bound.command == [helper.sys.executable, "-B", "-m", "pytest", "-c", str(repository / "pytest.ini"),
                             "-o", "addopts=", "-o", "cache_dir=" + str(run_root / "pytest-cache"),
                             "--rootdir=" + str(repository), "--confcutdir=" + str(repository),
                             "tests/fail_closed", "-q", "--basetemp", str(run_root / "p"),
                             "--", "--basetemp=literal-test-name"]
    assert child == {"Path": "admitted-fixture-path", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    assert environment == parent
    assert set(projection["removed_environment_keys"]) == set(parent) - {"Path"}
    assert projection["registered_argv"] == (helper.sys.executable, "-m", "pytest", *original)
    assert helper.find_explicit_basetemp(original) is None
    for rejected in (["--basetemp"], ["--basetemp="], ["--basetemp", "-q"],
                     ["--basetemp=x", "--basetemp=x"], ["--basetemp", "x", "--basetemp=y"]):
        with pytest.raises(ValueError):
            helper.build_pytest_invocation(rejected, fresh_basetemp=run_root / "p")
    for rejected in (["-o", "addopts=--basetemp=x"], ["--rootdir=x"], ["-p", "plugin"],
                     ["--noconftest"], ["@arguments"], ["--basetemp", str(tmp_path / "other")]):
        with pytest.raises(ValueError):
            helper._bind_canonical_pytest_invocation_v1(
                rejected, repository_root=repository, python_executable=helper.sys.executable,
                run_root=run_root, environment={})

    # Source-fixed report routes share one family table; no caller-selected scope.
    frozen_scopes = (
        (429, "QB", "pr166_qb_bounded_quantum_benchmark", "pr166_qb"),
        (431, "QC", "pr166_qc_quantum_selected_replay_paper_retest", "pr166_qc"),
        (433, "MAPPER", "pr162e_q_quantum_automapper", "pr162e_q"),
    )
    for first, family, domain, stem in frozen_scopes:
        prefix = "tests/stage1_prediction_markets/" + domain
        idem = prefix + "/test_" + stem + "_idempotence.py"
        for position, scope in ((first, (idem, "-q", "--durations=50")),
                (first + 1, (prefix, "-q", "--ignore", idem, "--durations=50"))):
            for temp_args in (("--basetemp", str(run_root / "p")),
                              ("--basetemp=" + str(run_root / "p"),)):
                command = (helper.sys.executable, "-B", "tools/run_pytest_fresh_basetemp.py", *scope, *temp_args)
                assert reliability._mapper_original_position_v1(command, repository) == position
                assert next(row[1] for row in reliability._REPORT_READ_ROUTES_V1 if row[0] == position) == family
                child = reliability._mapper_child_command_v1(command, repository, run_root)
                assert child[:3] == (helper.sys.executable, "-B", "-c")
                assert child[3] == reliability._MAPPER_PYTEST_BOOTSTRAP_V1
                assert child[-len(scope)-2:] == (*scope, "--basetemp", str(run_root / "p"))
            command = (helper.sys.executable, "tools/run_pytest_fresh_basetemp.py", *scope, "--basetemp", str(run_root / "p"))
            for bad in (command + ("-x",), command + ("-k", "one"),
                        command + ("--noconftest",), command + ("-p", "plugin"),
                        command + ("--", "extra"), command + ("--basetemp=x",),
                        command[:-2], command + ("--collect-only",)):
                with pytest.raises(ValueError):
                    reliability._mapper_original_position_v1(bad, repository)
    unrelated = (helper.sys.executable, "tools/run_pytest_fresh_basetemp.py", "tests/fail_closed", "-q", "--basetemp", str(run_root / "p"))
    assert reliability._mapper_original_position_v1(unrelated, repository) is None


def test_helper_does_not_duplicate_basetemp_when_separate_arg_supplied():
    custom_basetemp = str(_custom_basetemp())
    pytest_args = ["tests/fail_closed", "--basetemp", custom_basetemp, "-q"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.added_basetemp is False
    assert invocation.basetemp == custom_basetemp
    assert invocation.command[3:] == pytest_args
    assert invocation.command.count("--basetemp") == 1
    assert str(_fixed_basetemp()) not in invocation.command


def test_helper_does_not_duplicate_basetemp_when_equals_arg_supplied():
    custom_basetemp = str(_custom_basetemp())
    pytest_args = ["tests/fail_closed", f"--basetemp={custom_basetemp}", "-q"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.added_basetemp is False
    assert invocation.basetemp == custom_basetemp
    assert invocation.command[3:] == pytest_args
    assert not any(arg == "--basetemp" for arg in invocation.command)


def test_selected_fresh_basetemp_is_under_system_temp():
    basetemp = helper.make_fresh_basetemp(
        now=datetime(2026, 5, 8, 12, 34, 56, 123456, tzinfo=UTC),
        pid=4321,
    )

    assert basetemp.parent == Path(tempfile.gettempdir()) / "qtt_pytest_basetemp"
    assert basetemp.name == "pytest_20260508_123456_123456_4321"

    with tempfile.TemporaryDirectory(prefix="qtt-helper-root-") as temp_root:
        fixture_repo = Path(temp_root) / "fixture-repo"
        fixture_repo.mkdir()
        external_parent = Path(temp_root) / "external-process-root"
        first, first_probe = reliability.resolve_validation_run_paths(
            fixture_repo,
            explicit_process_root=external_parent.resolve(),
            run_id="run_helper_first",
            projected_relative_paths=("tests/fail_closed/deep/example/test_case.py",),
        )
        second, second_probe = reliability.resolve_validation_run_paths(
            fixture_repo,
            explicit_process_root=external_parent.resolve(),
            run_id="run_helper_second",
        )
        try:
            assert first.process_root != second.process_root
            assert first.process_root.name == first.process_child_name
            assert first.process_child_name != first.run_id
            assert re.fullmatch(
                r"r\d{12}_\d+_\d+(?:_\d+)?",
                first.process_child_name,
            )
            assert first.process_root_is_external_to_repo is True
            assert first.cleanup_target == first.process_root
            assert first.validation_output_root.name == (
                reliability.VALIDATION_OUTPUT_DIR_NAME
            )
            assert first.pytest_basetemp_root.name == (
                reliability.PYTEST_BASETEMP_DIR_NAME
            )
            assert first.deepest_projected_path == first_probe.write_path
            assert len(str(first_probe.renamed_path)) == len(
                str(first.deepest_projected_path)
            )
            assert first.deepest_projected_path.parts[
                len(first.process_root.parts)
            ] == reliability.PYTEST_BASETEMP_DIR_NAME
            assert first_probe.failure_operation is None
            assert second_probe.failure_operation is None
        finally:
            reliability.cleanup_validation_run(first)
            reliability.cleanup_validation_run(second)

    with pytest.raises(
        reliability.ValidationReliabilityError,
        match="ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
    ):
        reliability.resolve_validation_run_paths(
            helper.REPO_ROOT,
            explicit_process_root=helper.REPO_ROOT / ".tmp",
            run_id="run_helper_rejected",
        )


def test_selected_fresh_basetemp_is_short_and_windows_safe(monkeypatch):
    basetemp = helper.make_fresh_basetemp(
        now=datetime(2026, 5, 8, 12, 34, 56, 123456, tzinfo=UTC),
        pid=4321,
    )

    assert len(str(basetemp)) <= helper.MAX_BASETEMP_TEXT_LENGTH
    assert re.fullmatch(r"pytest_\d{8}_\d{6}_\d{6}_4321", basetemp.name)
    assert not any(char in basetemp.name for char in '<>:"/\\|?*')

    with tempfile.TemporaryDirectory(prefix="qtt-path-matrix-") as temp_root:
        root = Path(temp_root)
        fixture_repo = root / "fixture-repo"
        fixture_repo.mkdir()
        explicit = (root / "explicit").resolve()
        environment_root = (root / "environment").resolve()
        candidates = reliability._candidate_parents(
            explicit,
            environment={
                reliability.PROCESS_ROOT_ENV: str(environment_root),
                "SystemDrive": "Z:",
            },
            platform_name="nt",
        )
        assert [source for source, _path in candidates] == [
            "EXPLICIT",
            "ENVIRONMENT",
            "WINDOWS_SHORT_ROOT",
            "SYSTEM_TEMP",
        ]
        assert str(candidates[2][1]).replace("/", "\\") == "Z:\\qttv"

        environment_paths, _probe = reliability.resolve_validation_run_paths(
            fixture_repo,
            environment={reliability.PROCESS_ROOT_ENV: str(environment_root)},
            platform_name="posix",
            run_id="run_environment_precedence",
        )
        try:
            assert environment_paths.process_root.parent == environment_root
        finally:
            reliability.cleanup_validation_run(environment_paths)

        fallback_parent = root / "system-temp"
        fallback_parent.mkdir()
        with monkeypatch.context() as fallback_patch:
            fallback_patch.setattr(
                reliability.tempfile,
                "gettempdir",
                lambda: str(fallback_parent),
            )
            fallback_paths, _probe = reliability.resolve_validation_run_paths(
                fixture_repo,
                environment={},
                platform_name="posix",
                run_id="run_system_temp_fallback",
            )
        try:
            assert fallback_paths.process_root.parent == fallback_parent / "qttv"
        finally:
            reliability.cleanup_validation_run(fallback_paths)

        def failed_probe(process_root, *, deepest_projected_path, operation):
            probe_root = process_root / "filesystem-probe"
            return reliability.FilesystemProbeReceiptV1(
                probe_root=probe_root,
                created_directory=True,
                write_path=probe_root / "probe.bin",
                written_bytes=len(reliability.FILESYSTEM_PROBE_BYTES),
                readback_equal=False,
                renamed_path=probe_root / "probe-renamed.bin",
                rename_equal=False,
                unlink_success=False,
                directory_cleanup_success=False,
                failure_operation=operation,
                native_error_class="OSError",
            )

        for operation, code in (
            ("write_fsync", "ENGVR_FILESYSTEM_PROBE_FAILED"),
            ("deepest_projected_path", "ENGVR_LONGEST_PATH_PROBE_FAILED"),
        ):
            with monkeypatch.context() as failure_patch:
                failure_patch.setattr(
                    reliability,
                    "probe_run_filesystem",
                    lambda process_root, *, deepest_projected_path, value=operation: failed_probe(
                        process_root,
                        deepest_projected_path=deepest_projected_path,
                        operation=value,
                    ),
                )
                with pytest.raises(reliability.ValidationReliabilityError) as raised:
                    reliability.resolve_validation_run_paths(
                        fixture_repo,
                        explicit_process_root=(root / operation).resolve(),
                        run_id=f"run_{operation}",
                    )
                assert raised.value.code == code


def test_main_prints_basetemp_and_returns_pytest_exit_code(
    monkeypatch,
    capsys,
    tmp_path,
):
    # Synthetic substitutions below isolate the admitted allocation and taskkill
    # boundaries. They do not attest a real child or native tree termination.
    _exercise_rp5a_reader_hop_v1(monkeypatch, tmp_path)
    # The new real-child helper obeys the existing retention policy as well.
    # Only the supervisor is substituted below: it never starts a native child.
    # Existing path allocation/input checks and cleanup remain real.
    original_resolve = reliability.resolve_validation_run_paths
    original_cleanup = reliability.cleanup_validation_run
    for case, expected_cleanup in (("exception", False), ("unproven", False),
                                   ("terminal-failure", True), ("before-dispatch", True)):
        case_root = tmp_path / ("reader-retention-" + case)
        case_root.mkdir()
        allocated = []
        cleanup_calls = []
        dispatch_calls = []
        original_error = RuntimeError("synthetic reader-hop boundary failure")

        def recording_resolve(*args, **kwargs):
            result = original_resolve(*args, **kwargs)
            allocated.append(result[0])
            return result

        def recording_cleanup(paths):
            cleanup_calls.append(paths)
            return original_cleanup(paths)

        def no_child_supervisor(command, **kwargs):
            dispatch_calls.append(tuple(command))
            if case == "exception":
                raise original_error
            receipt = _command_receipt(
                command, kwargs, case_root,
                native_exit_code=0 if case == "unproven" else 1,
                failure_class=("ENGVR_PROCESS_TERMINATION_FAILED" if case == "unproven"
                               else "ENGVR_NATIVE_NONZERO_EXIT"),
                termination_state="TERMINAL:UNPROVEN" if case == "unproven" else "NOT_REQUIRED",
            )
            destination = Path(receipt.stderr_path)
            destination.parent.mkdir()
            destination.write_bytes(b"")
            return receipt

        def stop_before_dispatch(*args, **kwargs):
            raise original_error

        with monkeypatch.context() as fault:
            fault.setattr(reliability, "resolve_validation_run_paths", recording_resolve)
            fault.setattr(reliability, "cleanup_validation_run", recording_cleanup)
            fault.setattr(reliability, "supervise_command", no_child_supervisor)
            if case == "before-dispatch":
                fault.setattr(reliability, "write_run_provenance", stop_before_dispatch)
            expected_type = RuntimeError if case in {"exception", "before-dispatch"} else AssertionError
            with pytest.raises(expected_type) as observed:
                _exercise_rp5a_reader_hop_v1(fault, case_root)
        assert len(allocated) == 1
        assert len(dispatch_calls) == (0 if case == "before-dispatch" else 1)
        assert cleanup_calls == (allocated if expected_cleanup else [])
        assert allocated[0].process_root.exists() is not expected_cleanup
        if case in {"exception", "before-dispatch"}:
            assert observed.value is original_error
        if not expected_cleanup:
            # The explicit no-child substitution, not a production receipt,
            # proves this fault-injection fixture has no process to preserve.
            assert original_cleanup(allocated[0]) == "PASS_REMOVED_EXACT_RUN_ROOT"

    boundary_root = tmp_path / "focused-launch-boundaries"
    boundary_root.mkdir()
    fixture_repo = boundary_root / "repo"
    fixture_repo.mkdir()
    selected_parent = boundary_root / "selected"
    selected_parent.mkdir()

    def no_child(*args, **kwargs):
        pytest.fail("rejected allocation must not start a supervisor")

    for selected in (str(selected_parent), None):
        allocations = []

        def stop_at_allocation(repo, **kwargs):
            allocations.append((repo, kwargs))
            raise reliability.ValidationReliabilityError(
                "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
                "synthetic allocation-boundary stop",
            )

        with monkeypatch.context() as patch:
            patch.setattr(helper, "REPO_ROOT", fixture_repo)
            patch.delenv(reliability.RUN_ID_ENV, raising=False)
            patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
            if selected is None:
                patch.delenv(reliability.PROCESS_ROOT_ENV, raising=False)
            else:
                patch.setenv(reliability.PROCESS_ROOT_ENV, selected)
            patch.setattr(helper, "resolve_validation_run_paths", stop_at_allocation)
            patch.setattr(helper, "supervise_command", no_child)
            assert helper.main(["-q"]) == 1
        assert allocations == [
            (fixture_repo, {
                "explicit_process_root": selected,
                "projected_relative_paths": ("-q",),
            })
        ]
        output = capsys.readouterr()
        assert output.out == ""
        assert output.err.count("ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE") == 1

    linked_parent = boundary_root / "synthetic-junction"
    linked_parent.mkdir()
    ordinary_file = boundary_root / "ordinary-file"
    ordinary_file.write_bytes(b"fixture")
    for selected, code in (
        ("", "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE"),
        (" " + str(selected_parent), "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE"),
        (str(selected_parent) + " ", "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE"),
        ("relative-parent", "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED"),
        (str(selected_parent / ".." / "other"), "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED"),
        (str(linked_parent), "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED"),
        (str(ordinary_file), "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED"),
    ):
        allocations = []

        def unexpected_allocation(*args, **kwargs):
            allocations.append((args, kwargs))
            pytest.fail("invalid configured parent reached allocation")

        with monkeypatch.context() as patch:
            patch.setattr(helper, "REPO_ROOT", fixture_repo)
            patch.delenv(reliability.RUN_ID_ENV, raising=False)
            patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
            patch.setenv(reliability.PROCESS_ROOT_ENV, selected)
            patch.setattr(helper, "resolve_validation_run_paths", unexpected_allocation)
            patch.setattr(helper, "supervise_command", no_child)
            if selected == str(linked_parent):
                # This one path has a simulated junction observation; the real
                # path-chain validator still makes the rejection.
                real_is_junction = reliability._path_is_junction
                patch.setattr(
                    reliability, "_path_is_junction",
                    lambda path: path == linked_parent or real_is_junction(path),
                )
            assert helper.main(["-q"]) == 1
        assert allocations == []
        output = capsys.readouterr()
        assert output.out == ""
        assert output.err.count(code) == 1

    def no_default_enumeration(*args, **kwargs):
        pytest.fail("explicit parent enumerated a default candidate")

    with monkeypatch.context() as patch:
        patch.setattr(reliability, "_candidate_parents", no_default_enumeration)
        patch.setattr(reliability.tempfile, "gettempdir", no_default_enumeration)
        paths, probe = reliability.resolve_validation_run_paths(
            fixture_repo, explicit_process_root=str(selected_parent),
        )
        assert paths.process_root.parent == selected_parent
        assert paths.evidence_root.parent == selected_parent
        assert paths.pytest_basetemp_root.parent == paths.process_root
        assert paths.validation_output_root.parent == paths.process_root
        assert paths.process_root_is_external_to_repo is True
        assert probe.failure_operation is None
        assert reliability.cleanup_validation_run(paths).startswith("PASS")
        assert not paths.process_root.exists()
        assert paths.evidence_root.is_dir()

    admission_parent = boundary_root / "admission-denied"
    admission_parent.mkdir()
    admissions = []
    denied = reliability.ValidationReliabilityError(
        "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE", "synthetic explicit admission denial",
    )

    def deny_admission(candidate, repo):
        admissions.append((candidate, repo))
        raise denied

    with monkeypatch.context() as patch:
        patch.setattr(helper, "REPO_ROOT", fixture_repo)
        patch.delenv(reliability.RUN_ID_ENV, raising=False)
        patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
        patch.setenv(reliability.PROCESS_ROOT_ENV, str(admission_parent))
        patch.setattr(reliability, "_candidate_parents", no_default_enumeration)
        patch.setattr(reliability.tempfile, "gettempdir", no_default_enumeration)
        patch.setattr(reliability, "_validate_candidate_parent", deny_admission)
        patch.setattr(helper, "supervise_command", no_child)
        assert helper.main(["-q"]) == 1
    assert admissions == [(admission_parent, fixture_repo.resolve())]
    assert list(admission_parent.iterdir()) == []
    output = capsys.readouterr()
    assert output.out == ""
    assert "synthetic explicit admission denial" in output.err

    probe_parent = boundary_root / "probe-denied"
    probe_parent.mkdir()
    operations = []
    real_probe = reliability.probe_run_filesystem
    real_remove = reliability.remove_exact_run_owned_process_tree

    def failed_probe(process_root, **kwargs):
        operations.append(("probe", process_root))
        receipt = real_probe(process_root, **kwargs)
        assert receipt.failure_operation is None
        return reliability.replace(
            receipt, failure_operation="deepest_open",
            native_error_class="OSError",
        )

    def owned_remove(process_root, **kwargs):
        operations.append(("cleanup", process_root))
        assert kwargs["expected_run_root"] == process_root
        assert process_root.parent == probe_parent
        assert kwargs["repo_root"] == fixture_repo.resolve()
        assert kwargs["evidence_root"].parent == probe_parent
        return real_remove(process_root, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(helper, "REPO_ROOT", fixture_repo)
        patch.delenv(reliability.RUN_ID_ENV, raising=False)
        patch.delenv(reliability.EVIDENCE_ROOT_ENV, raising=False)
        patch.setenv(reliability.PROCESS_ROOT_ENV, str(probe_parent))
        patch.setattr(reliability, "_candidate_parents", no_default_enumeration)
        patch.setattr(reliability.tempfile, "gettempdir", no_default_enumeration)
        patch.setattr(reliability, "probe_run_filesystem", failed_probe)
        patch.setattr(reliability, "remove_exact_run_owned_process_tree", owned_remove)
        patch.setattr(helper, "supervise_command", no_child)
        assert helper.main(["-q"]) == 1
    assert len(operations) == 2
    assert operations[0][0] == "probe"
    assert operations[1] == ("cleanup", operations[0][1])
    assert list(probe_parent.iterdir()) == []
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.count("ENGVR_LONGEST_PATH_PROBE_FAILED") == 1

    generic_temp = boundary_root / "legacy-temp"
    generic_env = boundary_root / "legacy-environment"
    with monkeypatch.context() as patch:
        patch.setattr(reliability.tempfile, "gettempdir", lambda: str(generic_temp))
        assert reliability._candidate_parents(
            None,
            environment={reliability.PROCESS_ROOT_ENV: " " + str(generic_env) + " ",
                         "SystemDrive": "Z:"},
            platform_name="nt",
        ) == (
            ("ENVIRONMENT", generic_env),
            ("WINDOWS_SHORT_ROOT", Path("Z:/qttv")),
            ("SYSTEM_TEMP", generic_temp / "qttv"),
        )
        assert reliability._candidate_parents(
            selected_parent,
            environment={reliability.PROCESS_ROOT_ENV: str(generic_env),
                         "SystemDrive": "Z:"},
            platform_name="nt",
        ) == (
            ("EXPLICIT", selected_parent),
            ("ENVIRONMENT", generic_env),
            ("WINDOWS_SHORT_ROOT", Path("Z:/qttv")),
            ("SYSTEM_TEMP", generic_temp / "qttv"),
        )
        assert reliability._candidate_parents(
            None, environment={}, platform_name="posix",
        ) == (("SYSTEM_TEMP", generic_temp / "qttv"),)

    # Exercise the real termination-helper body with a simulated Popen child.
    # No Windows taskkill or operating-system process is started by these cases.
    taskkill_argv = ["taskkill", "/PID", "12345", "/T"]
    for case in ("zero", "nonzero", "timeout-terminal", "timeout-unknown", "kill-error"):
        calls = []
        timeout_first = reliability.subprocess.TimeoutExpired(
            taskkill_argv, reliability.TERMINATION_GRACE_SECONDS,
            output=b"first stdout", stderr=b"first stderr",
        )
        timeout_second = reliability.subprocess.TimeoutExpired(
            taskkill_argv, reliability.TERMINATION_GRACE_SECONDS,
            output=b"second stdout", stderr=b"second stderr",
        )
        kill_error = OSError("synthetic kill failure")

        class SimulatedTaskkill:
            pid = 12345
            returncode = None

            def communicate(self, *, timeout):
                calls.append(("communicate", timeout))
                count = sum(kind == "communicate" for kind, _ in calls)
                if case.startswith("timeout") or case == "kill-error":
                    if count == 1:
                        raise timeout_first
                    if case == "timeout-unknown":
                        raise timeout_second
                self.returncode = 19 if case == "nonzero" else 0
                return b"simulated stdout", b"simulated stderr"

            def kill(self):
                calls.append(("kill", None))
                if case == "kill-error":
                    raise kill_error

        child = SimulatedTaskkill()
        starts = []

        def simulated_popen(argv, **kwargs):
            starts.append((argv, kwargs))
            return child

        with monkeypatch.context() as patch:
            patch.setattr(reliability.subprocess, "Popen", simulated_popen)
            if case in {"timeout-unknown", "kill-error"}:
                with pytest.raises(reliability.ValidationReliabilityError) as raised:
                    reliability._hidden_taskkill(taskkill_argv)
                error = raised.value
                cause = timeout_second if case == "timeout-unknown" else kill_error
                assert error.code == "ENGVR_PROCESS_TERMINATION_FAILED"
                assert error.owned_process is child
                assert error.__cause__ is cause
                assert error.stdout_prefix == getattr(cause, "output", None)
                assert error.stderr_prefix == getattr(cause, "stderr", None)
                assert "PID=12345" in error.detail
                assert child.returncode is None
            else:
                expected = {"zero": 0, "nonzero": 19, "timeout-terminal": 124}[case]
                assert reliability._hidden_taskkill(taskkill_argv) == expected
                assert child.returncode == (19 if case == "nonzero" else 0)
        assert len(starts) == 1
        assert starts[0][0] == taskkill_argv
        actual_kwargs = dict(starts[0][1])
        expected_kwargs = {
            "shell": False,
            "stdin": reliability.subprocess.DEVNULL,
            "stdout": reliability.subprocess.PIPE,
            "stderr": reliability.subprocess.PIPE,
            "creationflags": int(getattr(reliability.subprocess, "CREATE_NO_WINDOW", 0)),
        }
        startup_class = getattr(reliability.subprocess, "STARTUPINFO", None)
        if startup_class is not None:
            assert set(actual_kwargs) == set(expected_kwargs) | {"startupinfo"}
            startup = actual_kwargs.pop("startupinfo")
            assert type(startup) is startup_class
            assert {
                "dwFlags": startup.dwFlags,
                "wShowWindow": startup.wShowWindow,
                "hStdInput": startup.hStdInput,
                "hStdOutput": startup.hStdOutput,
                "hStdError": startup.hStdError,
                "lpAttributeList": startup.lpAttributeList,
            } == {
                "dwFlags": int(getattr(reliability.subprocess, "STARTF_USESHOWWINDOW", 0)),
                "wShowWindow": int(getattr(reliability.subprocess, "SW_HIDE", 0)),
                "hStdInput": None,
                "hStdOutput": None,
                "hStdError": None,
                "lpAttributeList": {"handle_list": []},
            }
        assert actual_kwargs == expected_kwargs
        expected_calls = [("communicate", reliability.TERMINATION_GRACE_SECONDS)]
        if case.startswith("timeout") or case == "kill-error":
            expected_calls.append(("kill", None))
            if case != "kill-error":
                expected_calls.append(("communicate", reliability.TERMINATION_GRACE_SECONDS))
        assert calls == expected_calls

    seen: dict[str, object] = {}

    def fake_supervise(command, **kwargs):
        projection = reliability._COMMAND_PROJECTION_V1.get()
        seen["command"] = list(projection["registered_argv"])
        seen["effective_command"] = list(command)
        seen["projection"] = projection
        seen["kwargs"] = kwargs
        receipt = _command_receipt(
            command,
            kwargs,
            tmp_path,
            native_exit_code=7,
            failure_class="ENGVR_NATIVE_EXIT_NONZERO",
        )
        seen["receipt"] = receipt
        return receipt

    inherited_repo = tmp_path / "inherited-compatibility-repo"
    inherited_repo.mkdir()
    inherited_paths, inherited_probe = _attested_outer_run(
        inherited_repo,
        tmp_path / "inherited-compatibility-process-parent",
        "run_inherited",
    )
    inherited_payload = json.loads(
        (inherited_paths.evidence_root / "run.json").read_text(encoding="utf-8")
    )
    assert inherited_payload["run_id"] == inherited_paths.run_id
    assert inherited_payload["paths"]["repo_root"] == str(inherited_repo.resolve())
    assert inherited_payload["paths"]["evidence_root"] == str(
        inherited_paths.evidence_root
    )
    assert inherited_payload["paths"]["process_root"] == str(
        inherited_paths.process_root
    )
    assert inherited_payload["paths"]["pytest_basetemp_root"] == str(
        inherited_paths.pytest_basetemp_root
    )
    assert inherited_payload["filesystem_probe"] == reliability._json_compatible(
        inherited_probe
    )
    assert inherited_probe.failure_operation is None
    custom_basetemp = str(inherited_paths.pytest_basetemp_root)
    real_supervise_command = helper.supervise_command
    original_run_id = os.environ.get(reliability.RUN_ID_ENV)
    original_evidence_root = os.environ.get(reliability.EVIDENCE_ROOT_ENV)
    with monkeypatch.context() as inherited_patch:
        inherited_patch.setattr(helper, "REPO_ROOT", inherited_repo)
        # The surrounding pytest selection is not this in-process invocation.
        # Its unrelated arguments must not cause any descriptor acquisition.
        inherited_patch.setattr(helper.sys, "orig_argv", [helper.sys.executable, "-B", "-m",
            "pytest", "tests/pr168_rp5a/test_scan_is_bounded.py"])
        inherited_patch.setenv(reliability.RUN_ID_ENV, inherited_paths.run_id)
        inherited_patch.setenv(
            reliability.EVIDENCE_ROOT_ENV,
            str(inherited_paths.evidence_root),
        )
        inherited_patch.setattr(
            helper,
            "supervise_command",
            fake_supervise,
        )
        exit_code = helper.main(
            ["tests/fail_closed", "--basetemp", custom_basetemp, "-q"]
        )

        assert exit_code == 7
        assert seen["command"][1:3] == ["-m", "pytest"]
        assert seen["effective_command"][1:4] == ["-B", "-m", "pytest"]
        assert seen["effective_command"].count("--basetemp") == 1
        assert seen["kwargs"]["environment"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        assert seen["kwargs"]["environment"]["PYTHONDONTWRITEBYTECODE"] == "1"
        assert seen["kwargs"]["cwd"] == inherited_repo
        assert seen["kwargs"]["run_id"] == "run_inherited"
        assert seen["kwargs"]["phase"] == "nested-pytest"
        typed_receipt = seen["receipt"]
        assert isinstance(
            typed_receipt,
            reliability.CommandExecutionReceiptV1,
        )
        assert typed_receipt.native_exit_code == 7
        assert typed_receipt.failure_class == "ENGVR_NATIVE_EXIT_NONZERO"
        assert typed_receipt.start_failure_class is None
        assert typed_receipt.timeout_state == "NOT_CONFIGURED"
        assert typed_receipt.termination_state == "NOT_REQUIRED"
        assert typed_receipt.stdout_marker_state == "NOT_REQUIRED"
        inherited_output = capsys.readouterr()
        assert inherited_output.out == f"pytest basetemp: {custom_basetemp}\n"
        assert inherited_output.err == ""

    assert helper.supervise_command is real_supervise_command
    assert os.environ.get(reliability.RUN_ID_ENV) == original_run_id
    assert os.environ.get(reliability.EVIDENCE_ROOT_ENV) == original_evidence_root
    _assert_standalone_helper_receipt_matrix(monkeypatch, tmp_path, capsys)
    assert helper.supervise_command is real_supervise_command
    _assert_inherited_receipt_fail_closed_matrix(
        monkeypatch,
        capsys,
        tmp_path,
    )
    _assert_inherited_outer_run_attestation(monkeypatch, capsys, tmp_path)


def test_helper_introduces_no_blocked_behavior_terms():
    helper_text = Path(helper.__file__).read_text(encoding="utf-8").lower()

    for blocked_term in ["runtime", "live", "source", "order", "sha", "freeze", "profit"]:
        assert blocked_term not in helper_text
    assert ' / ".tmp"' not in helper_text
    assert "subprocess.run" not in helper_text
    assert "supervise_command" in helper_text

def _exercise_rp5a_reader_hop_v1(monkeypatch, tmp_path):
    import dataclasses
    import shutil
    import stat
    import sys
    import time
    from tools import pr168_rp5a_git_grep_scanner as scan_owner
    # Copy only this literal reached module closure into a finite toy repository.
    # The child fixture proves transport/context ownership, not RP5A data truth.
    closure = (
        "build_pr168_rp5a_legacy_semantic_audit.py", "ci_branch_context.py",
        "pr168_rp5a_agent_touchpoints.py", "pr168_rp5a_blast_radius.py",
        "pr168_rp5a_config.py", "pr168_rp5a_consumer_graph.py",
        "pr168_rp5a_cross_graph_consistency.py", "pr168_rp5a_delete_eligibility.py",
        "pr168_rp5a_git_grep_scanner.py", "pr168_rp5a_identity_custody.py",
        "pr168_rp5a_identity_dependency.py", "pr168_rp5a_json_scanner.py",
        "pr168_rp5a_pr_metadata_scanner.py", "pr168_rp5a_report_writer.py",
        "pr168_rp5a_row_field_hit_index.py", "pr168_rp5a_term_taxonomy.py",
        "pr168_rp5a_validation_dependency_graph.py", "repo_path_refs.py",
        "run_pytest_fresh_basetemp.py", "run_validation_gates.py", "validation_inventory.py",
        "validation_reliability.py", "validation_scope_registry.py",
    )
    root = tmp_path / "reader-hop-repo"
    (root / "tools").mkdir(parents=True)
    original_root = Path(helper.__file__).resolve().parents[1]
    for filename in closure:
        source = original_root / "tools" / filename
        assert source.is_file() and source.stat().st_nlink == 1
        (root / "tools" / filename).write_bytes(source.read_bytes())
    (root / "pytest.ini").write_bytes(b"[pytest]\n")
    import subprocess
    git_program = shutil.which("git")
    assert git_program is not None
    initialized = subprocess.run([git_program, "--no-optional-locks", "init", "-b", "main"],
        cwd=root, env=scan_owner._scan_child_environment(os.environ),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert initialized.returncode == 0, initialized.stderr

    selected = root / "tests/pr168_rp5a/test_reader_fixture.py"
    selected.parent.mkdir(parents=True)
    selected.write_text(
        "from tools.build_pr168_rp5a_legacy_semantic_audit import _require_builder_reads_v1\n"
        "def test_original_bound_reader():\n"
        "    context = _require_builder_reads_v1()\n"
        "    assert context.expected_baseline_ref == '1' * 40\n"
        "    assert context.ledger.invocations == 0\n"
        "    assert context.text(('branch', '--show-current')) == 'main'\n"
        "    assert context.ledger.invocations == 1\n"
        "    assert context.current_runner_source == context.expected_current_runner_source\n"
        "    assert context.scope_source == context.expected_scope_source\n",
        encoding="utf-8", newline="\n")
    paths, probe = reliability.resolve_validation_run_paths(
        root, explicit_process_root=(tmp_path / "reader-hop-parent").resolve(),
        run_id="run_synthetic_reader_hop", projected_relative_paths=(selected.relative_to(root).as_posix(),))
    receipt = None
    supervision_pending = False
    retained_errors = []
    try:
        for relative in ("reader", "input"):
            (paths.process_root / relative).mkdir()
        names = ("tools/run_validation_gates.py", "tools/validation_scope_registry.py")
        rows = tuple(reliability._ScanCandidateSurface(relative, "FILE",
            stat.S_IMODE((root / relative).stat().st_mode), (root / relative).read_bytes(), ()) for relative in names)
        limits = reliability._ScanRunReadLimits(4_000_000, 20000, 64, 1)
        deadline = time.monotonic_ns() + 180_000_000_000
        basis = reliability._Rp5aReadBasisV1("1" * 40, b"# synthetic historical data\n",
            1_048_576, 2, 256, 1_048_576, 10000, 100, 1000)
        argv = (sys.executable, "-B", str(root / "tools/run_pytest_fresh_basetemp.py"),
                "-q", selected.relative_to(root).as_posix(), "--basetemp", str(paths.pytest_basetemp_root))
        plan = reliability.build_command_evidence_plan(run_id=paths.run_id, phase="synthetic-reader-hop",
            commands=(argv,), cwd=root)
        executable = shutil.which("git")
        assert executable is not None
        executable = str(Path(executable).resolve())
        profile = reliability._Rp5aScanProfile(paths.run_id, 1, str(root), str(paths.process_root / "reader"),
            names, 2, sum(len(n.encode()) + 1 for n in names),
            tuple((row.path, len(row.content)) for row in rows), executable, executable, "git",
            tuple(scan_owner._scan_child_environment(os.environ).items()),
            8_388_608, limits.byte_limit + basis.stdout_bytes_per_call + 4096,
            4096, 16_777_216, deadline, 4)
        # Account worst-case one-byte frame progress and all three comparisons
        # for both original frames, plus original context/source/final checks.
        candidate_bytes = sum(len(row.content) for row in rows)
        allowance = candidate_bytes * (8 * (limits.byte_limit + 4) + 100)
        fence = reliability._ScanCandidateFence(root, rows, limits=limits,
            candidate_read_bytes=allowance, deadline_ns=deadline)
        identity = reliability._ScanLaunchIdentity(paths.run_id, "synthetic-reader-hop", 1, 1, argv, str(root))
        original_input = reliability._ScanLaunchInput(identity, rows, limits=limits,
            candidate_read_bytes=allowance, deadline_ns=deadline,
            scratch_root=paths.process_root / "input", scratch_bytes=limits.byte_limit + 4,
            parent_frame_reread_bytes=3 * (limits.byte_limit + 4), check_candidate=fence, rp5a_read_basis=basis)
        launch = reliability._prepare_scan_launch(paths, phase="synthetic-reader-hop", plan=plan,
            profiles={}, reader_profiles={1: profile}, reader_bases={1: basis}, launch_inputs={1: original_input},
            read_limits=limits, deadline_ns=deadline)
        assert launch.plan is plan and launch.reader_bases[1] is basis
        for kwargs in (
            {"reader_profiles": {}, "reader_bases": {1: basis}},
            {"reader_profiles": {1: profile}, "reader_bases": {}},
            {"reader_profiles": {1: profile, 2: dataclasses.replace(profile, command_index=2)},
             "reader_bases": {1: basis, 2: basis}},
        ):
            with pytest.raises(ValueError):
                reliability._prepare_scan_launch(paths, phase="synthetic-reader-hop", plan=plan,
                    profiles={}, launch_inputs={1: original_input}, read_limits=limits,
                    deadline_ns=deadline, **kwargs)
        reliability.write_run_provenance(paths, probe, phase="synthetic-reader-hop", command_count=1,
            text_integrity_preflight_state="NOT_APPLICABLE", rp5a_scan_profiles={},
            rp5a_reader_profiles=launch.reader_profiles, rp5a_reader_bases=launch.reader_bases)
        environment = reliability._scan_child_launch_environment(os.environ, launch=launch, planned=plan[0])
        environment.update({"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        with original_input:
            supervision_pending = True
            receipt = reliability.supervise_command(argv, cwd=root, run_id=paths.run_id,
                phase="synthetic-reader-hop", command_index=1, evidence_root=paths.evidence_root,
                environment=environment, launch_input=original_input, timeout_seconds=180,
                mirror_stdout=False, mirror_stderr=False)
            supervision_pending = reliability._command_requires_process_retention_v1(receipt)
        assert receipt.native_exit_code == 0 and receipt.failure_class is None, Path(receipt.stderr_path).read_bytes()
        assert original_input.state == "CLOSED"
        assert b"1 passed" in Path(receipt.stdout_path).read_bytes()
        nested_roots = tuple(paths.evidence_root.glob("nested-pytest-*"))
        assert len(nested_roots) == 1
        nested = json.loads((nested_roots[0] / "command-1.json").read_text())
        assert nested["run_id"] == paths.run_id and nested["phase"] == "nested-pytest" and nested["command_index"] == 1
        assert nested["native_exit_code"] == 0 and nested["failure_class"] is None
        assert nested["argv"][2:4] == ["-c", helper._RP5A_PYTEST_BOOTSTRAP_V1]
        assert sorted(p.name for p in (paths.process_root / "reader").iterdir()) == ["pytest-input", "pytest-reads"]
        assert all(not list(p.iterdir()) for p in (paths.process_root / "reader").iterdir())
        assert not list((paths.process_root / "input").iterdir())
    except BaseException as error:
        retained_errors.append(error)
    finally:
        retain = supervision_pending or (
            receipt is not None and reliability._command_requires_process_retention_v1(receipt)
        )
        if retain:
            if not retained_errors:
                retained_errors.append(reliability.ValidationReliabilityError(
                    "ENGVR_PROCESS_TERMINATION_FAILED",
                    "RP5A reader-hop fixture retains its run after unresolved supervision",
                ))
        else:
            try:
                assert reliability.cleanup_validation_run(paths) == "PASS_REMOVED_EXACT_RUN_ROOT"
            except BaseException as error:
                retained_errors.append(error)
    reliability._scan_raise_errors(retained_errors)
    assert not paths.process_root.exists()
