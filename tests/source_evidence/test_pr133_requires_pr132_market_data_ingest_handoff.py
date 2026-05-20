from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_requires_pr132_market_data_ingest_handoff():
    built = support.artifacts()
    assert built["pr132_handoff"]["handoff_id"] == "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1"
    assert support.validation_failures(built) == []
