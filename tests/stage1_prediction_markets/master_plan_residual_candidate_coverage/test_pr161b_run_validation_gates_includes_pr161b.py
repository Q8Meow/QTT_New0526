from pathlib import Path

from tools import run_validation_gates as runner


def test_pr161b_run_validation_gates_includes_pr161b_after_pr161a():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_pr161b_master_plan_residual_candidate_coverage.py" in command_names
    assert command_names.index("validate_pr161a_atomicrows_pr154_value_state_materialization.py") < command_names.index(
        "validate_pr161b_master_plan_residual_candidate_coverage.py"
    )
