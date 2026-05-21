from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_live_runtime_authority_market_fetch_rest_websocket_venue_api():
    assert_malformed("malformed_live_runtime_authority_created.v1.fixture.json", "LIVE_RUNTIME_AUTHORITY_CREATED")
    assert_malformed("malformed_live_market_data_fetch.v1.fixture.json", "LIVE_MARKET_DATA_FETCH_CREATED")

    for field_name, expected_code in (
        ("rest_client_created", "REST_CLIENT_CREATED"),
        ("websocket_client_created", "WEBSOCKET_CLIENT_CREATED"),
        ("venue_api_call_created", "VENUE_API_CALL_CREATED"),
        ("network_io_created", "NETWORK_IO_CREATED"),
    ):
        payload = mutable_artifacts()
        payload["runtime_resolver_input_locks"][0][field_name] = True
        assert expected_code in failure_codes(payload)
