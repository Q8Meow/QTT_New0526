from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_master_plan_consumed_not_edited():
    report = master_report()
    assert report["master_plan_consumed_confirmation"] is True
    assert report["master_plan_not_edited_confirmation"] is True
