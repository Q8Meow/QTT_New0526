from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_d_registry


def test_pr158_lane_d_pr154_owner_routes_internal_metadata_only():
    records = lane_d_registry()["records"]
    assert len(records) == 39
    assert all(record["owner_route_response_value"]["route_packet_class"] == "PR154_INTERNAL_OWNER_ROUTE_METADATA_ONLY" for record in records)
    assert all(record["live_blocked_until_owner_review"] is True for record in records)

