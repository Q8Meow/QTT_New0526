from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import count_receipt


def test_pr160_all_33_records_processed():
    assert count_receipt()["split_records_processed_count"] == 33
