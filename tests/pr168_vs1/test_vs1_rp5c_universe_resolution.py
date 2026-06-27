from __future__ import annotations

from ._helpers import rows


def test_vs1_rp5c_stage_agent_universe_uses_stage1_prediction_market_resolver():
    receipts = rows("stage_agent_universe_query_receipts.jsonl")
    selections = rows("context_formula_selection_receipts.jsonl")

    assert receipts
    assert all(row["market_family"] == "PREDICTION_MARKETS" for row in receipts)
    assert all(row["unknown_needs_review_count"] == 0 for row in receipts)
    assert all(10 <= row["selected_identity_count"] <= 50 for row in selections)
    assert all(row["no_unknown_needs_review_flag"] is True for row in selections)
