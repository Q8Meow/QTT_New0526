from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_live_market_data_fetch_rest_websocket_venue_api():
    for field in ("live_market_data_fetch_created", "rest_client_created", "websocket_client_created", "venue_api_call_created", "network_io_created"):
        built = support.cloned_artifacts()
        built["snapshot_input_locks"][0][field] = True
        assert any(field in failure for failure in support.validation_failures(built))
