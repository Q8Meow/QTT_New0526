from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import records


def test_pr160_each_record_has_exactly_one_final_route():
    assert all(item["one_final_route_flag"] is True for item in records())
    assert all(isinstance(item["final_route_class"], str) for item in records())
