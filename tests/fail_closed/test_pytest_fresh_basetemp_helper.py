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


def test_helper_preserves_user_pytest_args():
    pytest_args = ["tests/fail_closed", "-q", "-k", "scanner"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.command[3:-2] == pytest_args


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
        external_parent = Path(temp_root) / "external-process-root"
        first, first_probe = reliability.resolve_validation_run_paths(
            helper.REPO_ROOT,
            explicit_process_root=external_parent.resolve(),
            run_id="run_helper_first",
            projected_relative_paths=("tests/fail_closed/deep/example/test_case.py",),
        )
        second, second_probe = reliability.resolve_validation_run_paths(
            helper.REPO_ROOT,
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
            helper.REPO_ROOT,
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
                helper.REPO_ROOT,
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
                        helper.REPO_ROOT,
                        explicit_process_root=(root / operation).resolve(),
                        run_id=f"run_{operation}",
                    )
                assert raised.value.code == code


def test_main_prints_basetemp_and_returns_pytest_exit_code(
    monkeypatch,
    capsys,
    tmp_path,
):
    seen: dict[str, object] = {}

    def fake_supervise(command, **kwargs):
        seen["command"] = list(command)
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
