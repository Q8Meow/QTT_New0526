from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_private_doc_routes_require_attestation():
    assert report(c.PRIVATE_DOC_ROUTE_PATH)["record_count"] == 0
