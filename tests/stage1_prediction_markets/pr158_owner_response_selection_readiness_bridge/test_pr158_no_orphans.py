from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report


def test_pr158_no_orphans():
    assert master_report()["orphan_count"] == 0

