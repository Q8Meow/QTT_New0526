from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.enums import (
    RepairRoute,
)


def test_pr166_sm_repair_priority_is_ranked_and_routed(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RepairPriorityRegistry.report.json"]
    assert len(rows) == 3985
    ranks = [row["repair_priority_rank"] for row in rows]
    assert ranks == sorted(ranks)
    allowed_routes = {route.value for route in RepairRoute}
    for row in rows[:300]:
        assert 0.0 <= row["repair_priority_score"] <= 1.0
        assert row["repair_route"] in allowed_routes
        assert row["repair_route_ref"] == row["repair_route"]
        assert row["exact_missing_field"]
        assert row["materialization_action"]
