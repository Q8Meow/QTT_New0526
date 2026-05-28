from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records


def test_pr160_no_optimizer_execution():
    assert master_report()["optimizer_execution_count"] == 0
    assert all(item["optimizer_execution_created_flag"] is False for item in records())
