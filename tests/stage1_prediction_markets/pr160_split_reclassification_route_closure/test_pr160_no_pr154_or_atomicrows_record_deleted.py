from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import count_receipt


def test_pr160_no_pr154_or_atomicrows_record_deleted():
    receipt = count_receipt()
    assert receipt["total_pr154_universe_count"] == 342
    assert receipt["total_atomicrows_universe_count"] == 4183
