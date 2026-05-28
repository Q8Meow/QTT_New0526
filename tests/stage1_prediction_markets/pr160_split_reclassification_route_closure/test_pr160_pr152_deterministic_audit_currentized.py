from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import constants as pr152
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT


def test_pr160_pr152_deterministic_audit_currentized():
    path = ROOT / pr152.REPORT_PATH
    assert path.exists()
