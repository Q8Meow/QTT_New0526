from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_owner_decision_packet_for_ambiguous_routes():
    packet = report(c.OWNER_DECISION_PACKET_PATH)
    assert packet["decision_required_count"] == 0
    assert packet["owner_response_file_created_by_PR160_flag"] is False
