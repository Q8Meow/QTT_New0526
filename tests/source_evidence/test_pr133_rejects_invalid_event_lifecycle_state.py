from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_invalid_event_lifecycle_state():
    built = support.cloned_artifacts()
    built["event_state_snapshots"][0]["event_states"][0]["qtt_internal_lifecycle_state_class"] = "INVALID"
    assert any("invalid event lifecycle" in failure for failure in support.validation_failures(built))
