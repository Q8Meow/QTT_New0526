from ._helpers import rows


def test_no_trade_is_snapshot_scoped() -> None:
    for row in rows("notrade_rank.jsonl"):
        assert row["formula_global_ban_flag"] is False
        assert row["qku_global_ban_flag"] is False
        assert row["condition_scoped_memory_required_flag"] is True

