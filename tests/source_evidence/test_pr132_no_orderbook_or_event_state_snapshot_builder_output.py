from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_orderbook_or_event_state_snapshot_builder_output():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["orderbook_snapshot_created_count"] == 0
    assert evidence["event_state_snapshot_created_count"] == 0
    for event in support.canonical_events():
        assert event["adapter_output_is_orderbook_snapshot"] is False
        assert event["adapter_output_is_event_state_snapshot"] is False
