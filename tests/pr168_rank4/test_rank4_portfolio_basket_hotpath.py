from ._helpers import rows


def test_portfolio_basket_and_hotpath_are_advisory_only() -> None:
    for row in rows("rank_port_basket.jsonl"):
        assert row["basket_trade_authority_created_flag"] is False
        assert row["paper_order_intent_created_flag"] is False
    for row in rows("rank_hotpath.jsonl"):
        assert row["hotpath_ready_for_RANK4_advisory_only_flag"] is True
        assert row["hotpath_order_authority_created_flag"] is False

