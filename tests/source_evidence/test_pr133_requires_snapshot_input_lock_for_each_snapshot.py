from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_requires_snapshot_input_lock_for_each_snapshot():
    built = support.cloned_artifacts()
    built["orderbook_snapshots"][0]["snapshot_input_lock_ref"] = "PR133_MISSING_LOCK"
    assert any("missing input lock" in failure for failure in support.validation_failures(built))
