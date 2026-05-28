from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report


def test_pr158_master_plan_consumed_not_edited():
    report = master_report()
    assert report["master_plan_consumed_confirmation"] is True
    assert report["master_plan_not_edited_confirmation"] is True

