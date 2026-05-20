from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_preserves_quantum_metadata_only():
    report = support.main_report()["PR133_QUANTUM_METADATA_ONLY_EVIDENCE"]
    assert report["quantum_backend_simulator_optimizer_execution_count"] == 0
    assert report["quantum_snapshot_feature_computation_count"] == 0
    assert report["quantum_optimizer_input_created"] is False
    assert report["quantum_trading_signal_created"] is False
