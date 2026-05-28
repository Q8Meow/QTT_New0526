from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_low_latency_update_metadata_only():
    records = report(c.LOW_LATENCY_UPDATE_PATH)["records"]
    assert len(records) == 33
    assert all(item["low_latency_precomputed_index_metadata_only_flag"] is True for item in records)
