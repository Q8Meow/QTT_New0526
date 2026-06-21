from tools.pr168_data1_validator import run_validation


def test_pr168_data1_operator_action_matrix_is_actionable() -> None:
    run_validation("operator_action_matrix_is_actionable")
