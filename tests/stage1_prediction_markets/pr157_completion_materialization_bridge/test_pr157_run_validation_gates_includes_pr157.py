from pathlib import Path

from tools import run_validation_gates


def test_pr157_run_validation_gates_includes_pr157():
    names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py" in names
