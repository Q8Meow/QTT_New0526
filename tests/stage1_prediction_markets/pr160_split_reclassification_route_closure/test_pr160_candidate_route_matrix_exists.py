from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT, report


def test_pr160_candidate_route_matrix_exists():
    assert (ROOT / c.CANDIDATE_ROUTE_MATRIX_PATH).exists()
    assert report(c.CANDIDATE_ROUTE_MATRIX_PATH)["record_count"] == 33
