from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_connector_runtime_routes_do_not_create_semantics_or_receipts():
    records = report(c.CONNECTOR_RUNTIME_ROUTE_PATH)["records"]
    assert len(records) == 3
    assert all(item["connector_semantic_binding_created_by_PR160_flag"] is False for item in records)
    assert all(item["runtime_receipt_created_by_PR160_flag"] is False for item in records)
