from ._helpers import rows


def test_variable_tuning_uses_mutable_trade_variables_only() -> None:
    row = rows("var_tune_frontier.jsonl")[0]
    assert "VARIABLE_TUNING_FRONTIER" in row["frontier_class"]
    assert row["formula_global_ban_flag"] is False
    assert row["qku_global_ban_flag"] is False
