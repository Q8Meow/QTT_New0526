from ._helpers import rows


def test_auto_path_is_future_only() -> None:
    for row in rows("rank_auto_trading_path.jsonl"):
        assert row["paper_order_intent_created_by_RANK4"] is False
        assert row["live_order_authority_created_by_RANK4"] is False
        assert row["buy_sell_open_close_logic_created_by_RANK4"] is False

