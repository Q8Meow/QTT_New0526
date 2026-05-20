from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_rest_websocket_or_venue_api_clients():
    value = support.cloned_artifacts()
    record = value["adapter_report"]["venue_market_data_adapter_inputs"][0]
    record["rest_client_created"] = True
    record["websocket_client_created"] = True
    record["venue_api_call_created"] = True

    failures = support.validation_failures(value)

    assert any("rest_client_created" in failure for failure in failures)
    assert any("websocket_client_created" in failure for failure in failures)
    assert any("venue_api_call_created" in failure for failure in failures)
