from ._helpers import rows


def test_no_trade_is_reoptimization_trigger_not_dead_end() -> None:
    assert rows("notrade_batch.jsonl")[0]["terminal_no_trade_dead_end_allowed"] is False
    agenda = rows("notrade_reopt.jsonl")[0]
    assert agenda["terminal_dead_end_flag"] is False
    assert agenda["agent_work_stops_flag"] is False
    assert agenda["formula_global_ban_flag"] is False
    assert agenda["qku_global_ban_flag"] is False
