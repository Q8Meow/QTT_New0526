from ._helpers import read_jsonl


def test_tca_readiness_decomposes_components_without_fee_or_tick_facts() -> None:
    rows = read_jsonl("tca_ready.jsonl")
    assert rows
    required = {
        "fee_model_presence",
        "spread_model_presence",
        "slippage_model_presence",
        "latency_model_presence",
        "market_impact_or_capacity_model_presence",
        "venue_tick_size_readiness",
        "min_order_size_readiness",
        "cashflow_semantics_readiness",
    }
    for row in rows[:10]:
        assert required <= row.keys()
        assert row["tca_ready_for_future_rp5g_flag"] is True
