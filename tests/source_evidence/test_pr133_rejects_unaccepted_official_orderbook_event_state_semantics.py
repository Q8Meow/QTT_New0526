from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_unaccepted_official_orderbook_event_state_semantics():
    built = support.cloned_artifacts()
    built["orderbook_snapshots"][0]["official_venue_semantics_fabricated"] = True
    assert any("official_venue_semantics_fabricated" in failure for failure in support.validation_failures(built))
