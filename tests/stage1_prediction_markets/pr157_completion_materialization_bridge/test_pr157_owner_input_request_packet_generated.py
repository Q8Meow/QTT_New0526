from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import owner_packet


def test_pr157_owner_input_request_packet_generated():
    packet = owner_packet()
    assert packet["packet_id"] == "PR157_OWNER_COMPLETION_INPUT_REQUEST_PACKET"
    assert packet["request_count"] == len(packet["requests"])
    assert packet["request_count"] > 0
