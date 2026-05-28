from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_a_registry, master_report


def test_pr158_lane_a_exact_agent_ids_only_when_uniquely_supported():
    assert master_report()["lane_summary_counts"]["lane_a"]["exact_agent_id_uniquely_supported_count"] == 0
    assert all(record["exact_agent_id_or_null"] is None for record in lane_a_registry()["records"])

