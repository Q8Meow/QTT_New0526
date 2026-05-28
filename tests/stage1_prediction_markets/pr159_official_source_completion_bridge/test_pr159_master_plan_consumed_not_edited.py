from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_master_plan_consumed_not_edited():
    report = master_report()
    assert report["master_plan_consumed_confirmation"] is True
    assert report["master_plan_not_edited_confirmation"] is True

