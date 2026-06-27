from __future__ import annotations

from ._helpers import rows


def test_vs1_ranking_and_champion_challenger_emit_diversified_topk_previews():
    rankings = rows("execution_adjusted_ranking_receipts.jsonl")
    champions = rows("champion_challenger_selection_receipts.jsonl")
    previews = rows("paper_intent_candidate_previews.jsonl")

    assert any(row["selection_status"] == "TOP_K_ELIGIBLE" and int(row["rank"]) == 1 for row in rankings)
    assert any(row["champion_trade_plan_id"] for row in champions)
    assert all(len(set(row["challenger_trade_plan_ids"])) == len(row["challenger_trade_plan_ids"]) for row in champions)
    assert all(row["paper_ready_preview_flag"] is True for row in previews)
