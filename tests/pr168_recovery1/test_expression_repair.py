from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_expression_repair_uses_safe_parser_not_eval() -> None:
    assert_recovery1_valid()
    assert len(rows("expression_repair")) == 7
    assert all(not row["unsafe_eval_used_flag"] for row in rows("expression_repair"))
