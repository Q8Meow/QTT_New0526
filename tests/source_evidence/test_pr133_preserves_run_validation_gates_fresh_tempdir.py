from pathlib import Path

from tools import run_validation_gates as runner


def test_pr133_preserves_run_validation_gates_fresh_tempdir(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    pytest_basetemp = Path(".tmp") / "run_validation_gates_pytest_pr133"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    commands = runner.build_validation_commands(pytest_basetemp=pytest_basetemp)
    names = [Path(command[1]).name for command in commands]
    assert names.index("venue_market_data_ingest_adapters_validate.py") < names.index("orderbook_event_state_snapshot_builder_validate.py")
    assert commands[-1][-1] == str(pytest_basetemp)
