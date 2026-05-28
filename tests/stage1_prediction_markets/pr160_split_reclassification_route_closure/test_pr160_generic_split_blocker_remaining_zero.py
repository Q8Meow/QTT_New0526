from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import count_receipt


def test_pr160_generic_split_blocker_remaining_zero():
    assert count_receipt()["generic_split_blocker_remaining_count"] == 0
