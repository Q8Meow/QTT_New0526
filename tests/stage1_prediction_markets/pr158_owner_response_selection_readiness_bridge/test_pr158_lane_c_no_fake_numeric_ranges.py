from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_c_registry


def test_pr158_lane_c_no_fake_numeric_ranges():
    assert all(record["actual_numeric_range_available"] is False for record in lane_c_registry()["records"])
    assert all(record["response_value_or_null"].startswith("CONSERVATIVE_") for record in lane_c_registry()["records"])

