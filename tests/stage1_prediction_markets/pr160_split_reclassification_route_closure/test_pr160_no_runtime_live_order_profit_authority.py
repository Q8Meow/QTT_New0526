from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, no_authority_values


def test_pr160_no_runtime_live_order_profit_authority():
    report = master_report()
    assert report["runtime_live_order_profit_authority_count"] == 0
    assert set(no_authority_values()) == {False}
