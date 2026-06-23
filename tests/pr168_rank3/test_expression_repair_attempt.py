from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_all_expression_repair_formulas_attempted_without_eval() -> None:
    assert_rank3_valid()
    attempts = rows("expression_repair_attempt")
    assert len(attempts) == 7
    assert all(row["repair_attempted_flag"] for row in attempts)
    assert all(row["unsafe_eval_executed_flag"] is False for row in attempts)
