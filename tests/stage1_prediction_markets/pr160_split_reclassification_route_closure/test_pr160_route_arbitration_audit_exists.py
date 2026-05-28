from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT, report


def test_pr160_route_arbitration_audit_exists():
    assert (ROOT / c.ARBITRATION_AUDIT_PATH).exists()
    assert report(c.ARBITRATION_AUDIT_PATH)["record_count"] == 33
