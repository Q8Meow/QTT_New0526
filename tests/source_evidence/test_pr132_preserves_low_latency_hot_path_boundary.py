from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_preserves_low_latency_hot_path_boundary():
    evidence = support.main_report()["PR132_LOW_LATENCY_BOUNDARY_EVIDENCE"]

    assert evidence["creates_precomputed_adapter_contracts_only"] is True
    assert evidence["runs_in_live_hot_path"] is False
    assert evidence["live_hot_path_network_call_created"] is False
    assert evidence["live_quote_freshness_claim_created"] is False
    assert evidence["future_hot_path_consumption_requires_later_authorization"] is True
    for event in support.canonical_events():
        assert event["future_hot_path_snapshot_ref"].startswith("FUTURE_HOT_PATH")
