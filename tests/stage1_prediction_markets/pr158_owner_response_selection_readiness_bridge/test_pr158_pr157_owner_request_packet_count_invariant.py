from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import owner_packet


def test_pr158_pr157_owner_request_packet_count_invariant():
    packet = owner_packet()
    assert packet["request_count"] == c.EXPECTED_OWNER_PACKET_REQUESTS
    assert len(packet["requests"]) == c.EXPECTED_OWNER_PACKET_REQUESTS

