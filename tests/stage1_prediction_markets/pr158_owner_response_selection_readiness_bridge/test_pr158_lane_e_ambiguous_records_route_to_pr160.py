from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_e_registry


def test_pr158_lane_e_ambiguous_records_route_to_pr160():
    assert all(record["future_route"] == c.FutureRoute.PR160_SPLIT_RECLASSIFICATION.value for record in lane_e_registry()["records"])

