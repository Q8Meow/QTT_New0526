from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_e_registry, master_report


def test_pr158_lane_e_split_reclassification_deterministic_only():
    assert master_report()["lane_summary_counts"]["lane_e"]["deterministically_reclassified_count"] == 0
    assert all(record["deterministic_basis_flag"] is False for record in lane_e_registry()["records"])
    assert all(record["response_value_or_null"] is None for record in lane_e_registry()["records"])

