from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_a_registry, master_report


def test_pr158_lane_a_defer_exact_agent_id_to_pr163_when_ambiguous():
    assert master_report()["lane_summary_counts"]["lane_a"]["exact_agent_id_deferred_to_PR163_count"] == 270
    assert all(record["defer_exact_agent_id_to_PR163"] is True for record in lane_a_registry()["records"])

