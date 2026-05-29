from pathlib import Path

from tools import run_validation_gates as runner


def test_pr161a_run_validation_gates_includes_pr161a_after_pr159s():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_pr161a_atomicrows_pr154_value_state_materialization.py" in command_names
    assert command_names.index("validate_pr159s_open_intake_completion.py") < command_names.index(
        "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
    )

