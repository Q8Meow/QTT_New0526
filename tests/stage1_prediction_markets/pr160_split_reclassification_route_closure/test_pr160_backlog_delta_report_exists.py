from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT, report


def test_pr160_backlog_delta_report_exists():
    assert (ROOT / c.BACKLOG_DELTA_PATH).exists()
    assert report(c.BACKLOG_DELTA_PATH)["post_PR160_generic_split_reclassification_count"] == 0
