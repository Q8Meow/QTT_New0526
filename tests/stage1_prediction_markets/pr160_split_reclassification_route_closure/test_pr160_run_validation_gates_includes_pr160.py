from pathlib import Path

from tools import run_validation_gates as runner


def test_pr160_run_validation_gates_includes_pr160():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_pr160_split_reclassification_route_closure.py" in command_names
    assert command_names.index("validate_pr159_official_source_completion_bridge.py") < command_names.index("validate_pr160_split_reclassification_route_closure.py")
