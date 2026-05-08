from pathlib import Path

from tools import run_validation_gates as runner


def _expected_commands(python_executable: str) -> list[list[str]]:
    validation_dir = Path(".tmp") / "validation_gates"
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    master_plan = Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    return [
        [
            python_executable,
            str(Path("tools") / "master_plan_ingest.py"),
            "--input",
            str(master_plan),
            "--section-manifest-out",
            str(section_manifest),
            "--traceability-out",
            str(traceability_report),
            "--scope-report-out",
            str(first_pr_scope_report),
        ],
        [
            python_executable,
            str(Path("tools") / "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_static.py"),
            "--schema",
            str(Path("schemas") / "source_evidence" / "source_evidence.schema.json"),
            "--owner-packet",
            str(
                Path("docs")
                / "master_plan"
                / "source_evidence"
                / "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_no_runtime_artifacts.py"),
            "--repo-root",
            ".",
            "--forbid-source-retrieval",
            "--forbid-source-acceptance",
            "--forbid-connector-binding",
            "--forbid-private-state-fetch",
            "--forbid-order-execution",
            "--forbid-neural-training",
            "--forbid-neural-inference",
            "--forbid-external-repo-clone",
            "--forbid-package-install-scripts",
        ],
        [
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            "-q",
        ],
    ]


def test_runner_builds_expected_command_sequence(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    assert runner.build_validation_commands() == _expected_commands(python_executable)


def test_runner_commands_use_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands
    assert all(command[0] == python_executable for command in commands)


def test_runner_invokes_pytest_through_fresh_basetemp_helper(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands[-1] == [
        python_executable,
        str(Path("tools") / "run_pytest_fresh_basetemp.py"),
        "-q",
    ]


def test_runner_does_not_use_direct_python_m_pytest(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(command[:3] == [python_executable, "-m", "pytest"] for command in commands)


def test_runner_does_not_use_direct_pytest_command(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(
        Path(token).name.lower() in {"pytest", "pytest.exe"}
        for command in commands
        for token in command
    )


def test_runner_includes_no_runtime_artifact_flags(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    no_runtime_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_no_runtime_artifacts.py")
    )

    assert "--forbid-source-retrieval" in no_runtime_command
    assert "--forbid-source-acceptance" in no_runtime_command
    assert "--forbid-connector-binding" in no_runtime_command
    assert "--forbid-private-state-fetch" in no_runtime_command
    assert "--forbid-order-execution" in no_runtime_command
    assert "--forbid-neural-training" in no_runtime_command
    assert "--forbid-neural-inference" in no_runtime_command
    assert "--forbid-external-repo-clone" in no_runtime_command
    assert "--forbid-package-install-scripts" in no_runtime_command


def test_runner_stops_on_first_failure_and_returns_failing_exit_code(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [["python", "gate_a.py"], ["python", "gate_b.py"], ["python", "gate_c.py"]]
    returncodes = [0, 9, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 9
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_returns_zero_when_all_mocked_commands_pass(monkeypatch, capsys):
    class Completed:
        returncode = 0

    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.main([])

    assert exit_code == 0
    assert seen == runner.build_validation_commands()
    assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER
