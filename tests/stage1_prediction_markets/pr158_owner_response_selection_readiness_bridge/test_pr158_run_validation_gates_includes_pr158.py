from pathlib import Path

from tools import run_validation_gates as runner


def test_pr158_run_validation_gates_includes_pr158():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_pr158_owner_response_selection_readiness_bridge.py" in command_names
    assert command_names.index("validate_pr157_pr154_atomicrows_completion_materialization_bridge.py") < command_names.index("validate_pr158_owner_response_selection_readiness_bridge.py")

