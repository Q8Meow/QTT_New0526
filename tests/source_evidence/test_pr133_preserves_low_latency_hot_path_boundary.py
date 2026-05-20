from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_preserves_low_latency_hot_path_boundary():
    boundary = support.main_report()["PR133_LOW_LATENCY_BOUNDARY_EVIDENCE"]
    assert boundary["precomputed_snapshot_contracts_only"] is True
    assert boundary["live_hot_path_execution_created"] is False
    assert boundary["future_hot_path_snapshot_ref_created_as_metadata_only"] is True
