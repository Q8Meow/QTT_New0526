from ._helpers import assert_rows_have_contract


def test_prediction_market_edge_hint_families_are_inputs_only() -> None:
    rows = assert_rows_have_contract("pm_edge_hints.jsonl")
    families = {row["hint_family"] for row in rows}

    assert "fee_adjusted_yes_no_complement_parity_hint" in families
    assert "cross_venue_price_dislocation_hint" in families
    assert "orderbook_imbalance_hint" in families
    assert "liquidity_decay_hint" in families
    assert "source_update_or_news_sensitivity_hint" in families
    assert all(row["future_rp5g_required_flag"] is True for row in rows)
    assert all(row["profit_proof_flag"] is False for row in rows)

