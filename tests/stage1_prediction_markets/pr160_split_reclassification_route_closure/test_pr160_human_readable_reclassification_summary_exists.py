from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT


def test_pr160_human_readable_reclassification_summary_exists():
    path = ROOT / c.HUMAN_SUMMARY_PATH
    assert path.exists()
    assert "Final route counts" in path.read_text(encoding="utf-8")
