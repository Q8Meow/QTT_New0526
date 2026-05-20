from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_runtime_resolver_snapshot_or_historical_dataset_digest():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["runtime_resolver_snapshot_created_count"] == 0
    assert evidence["historical_dataset_digest_created_count"] == 0
    for event in support.canonical_events():
        assert event["adapter_output_is_runtime_resolver_snapshot"] is False
        assert event["adapter_output_is_historical_dataset"] is False
