from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_source_required_routes_to_pr159r_without_source_acceptance():
    records = report(c.PR159R_SOURCE_REQUEUE_PATH)["records"]
    assert len(records) == 3
    assert all(item["accepted_source_packet_created_by_PR160_flag"] is False for item in records)
    assert all(item["accepted_value_created_by_PR160_flag"] is False for item in records)
