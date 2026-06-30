from ._helpers import rows


def test_best_next_action_routes_candidates() -> None:
    actions = {row["best_next_action"] for row in rows("rank_next_action.jsonl") if row.get("best_next_action")}
    assert actions
    assert actions <= {"ADVISORY_TOPK_FOR_QOPT1", "ADVISORY_TOPK_FOR_VS2_PAPER_PRIORITY", "MEMORY_PRIOR_SEED_FOR_MEM1", "LEARNING_RETEST_PRIORITY", "REPAIR_RETEST_PRIORITY", "NO_TRADE_FOR_SNAPSHOT", "QOPT_FRONTIER_CHALLENGER", "SHADOW_ROUTE_FUTURE_ONLY", "LIVE_LADDER_FUTURE_ONLY"}

