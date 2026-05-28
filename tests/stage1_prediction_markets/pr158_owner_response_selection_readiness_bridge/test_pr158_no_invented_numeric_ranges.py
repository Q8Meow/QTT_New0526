from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_c_registry, master_report


def test_pr158_no_invented_numeric_ranges():
    assert master_report()["invented_numeric_range_count"] == 0
    assert all(record["actual_numeric_range_available"] is False for record in lane_c_registry()["records"])

