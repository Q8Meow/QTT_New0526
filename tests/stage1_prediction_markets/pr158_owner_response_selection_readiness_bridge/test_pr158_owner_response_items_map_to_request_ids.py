from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import owner_packet, owner_response


def test_pr158_owner_response_items_map_to_request_ids():
    request_ids = {item["request_id"] for item in owner_packet()["requests"]}
    response_ids = [item["request_id"] for item in owner_response()["response_items"]]
    assert response_ids
    assert set(response_ids).issubset(request_ids)
    assert len(response_ids) == len(set(response_ids))

