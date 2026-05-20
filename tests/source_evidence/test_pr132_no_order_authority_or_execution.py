from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_order_authority_or_execution():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["order_authority_count"] == 0
    assert evidence["order_execution_count"] == 0
    for event in support.canonical_events():
        assert event["adapter_output_is_order_authority"] is False
        assert event["no_order_authority"] is True
