from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_venue_scope_mismatch():
    built = support.cloned_artifacts()
    built["pr132_handoff"]["venue_specific_scope"] = ["KALSHI", "POLYMARKET"]
    assert any("three Stage-1 venues" in failure for failure in support.validation_failures(built))
