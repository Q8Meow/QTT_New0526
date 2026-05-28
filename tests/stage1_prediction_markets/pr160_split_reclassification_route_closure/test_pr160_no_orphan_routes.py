from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import count_receipt, records


def test_pr160_no_orphan_routes():
    assert count_receipt()["orphan_route_count"] == 0
    assert all(item["required_actor"] and item["future_pr_route"] for item in records())
