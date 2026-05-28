from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import count_receipt


def test_pr160_split_reclassification_count_33():
    assert count_receipt()["pr154_split_reclassification_input_count"] == 33
