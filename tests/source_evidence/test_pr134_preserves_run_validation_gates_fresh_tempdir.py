from pathlib import Path

from tools import run_validation_gates as runner


def test_pr134_preserves_run_validation_gates_fresh_tempdir(monkeypatch, tmp_path):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    commands = runner.build_validation_commands(pytest_basetemp=tmp_path / "pytest")
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]

    pr133_index = command_names.index("orderbook_event_state_snapshot_builder_validate.py")
    pr134_index = command_names.index("runtime_resolver_snapshot_executor_validate.py")
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert pr133_index < pr134_index < connector_index
    assert commands[pr134_index] == [
        python_executable,
        str(Path("tools") / "runtime_resolver_snapshot_executor_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]
