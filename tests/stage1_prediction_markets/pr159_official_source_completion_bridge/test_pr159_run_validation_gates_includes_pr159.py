from pathlib import Path

from tools import run_validation_gates as runner


def test_pr159_run_validation_gates_includes_pr159():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_pr159_official_source_completion_bridge.py" in command_names
    assert command_names.index("validate_pr158_owner_response_selection_readiness_bridge.py") < command_names.index("validate_pr159_official_source_completion_bridge.py")

