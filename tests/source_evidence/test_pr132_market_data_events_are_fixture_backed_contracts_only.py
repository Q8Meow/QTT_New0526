from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_market_data_events_are_fixture_backed_contracts_only():
    assert support.adapter_report()["fixture_payloads_are_synthetic"] is True
    for record in support.adapter_inputs():
        assert record["fixture_payload_is_synthetic"] is True
        assert record["fixture_payload_contains_live_market_data"] is False
        assert record["fixture_payload_contains_official_venue_semantic_values"] is False
    for event in support.canonical_events():
        assert event["normalized_payload_class"] == "QTT_INTERNAL_FIXTURE_METADATA_ENVELOPE"
        assert event["no_live_fetch"] is True
