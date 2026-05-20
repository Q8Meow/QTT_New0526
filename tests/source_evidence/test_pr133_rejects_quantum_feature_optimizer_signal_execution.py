from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_quantum_feature_optimizer_signal_execution():
    for field in ("quantum_snapshot_feature_computation_created", "quantum_optimizer_input_created", "quantum_trading_signal_created", "quantum_execution_created"):
        built = support.cloned_artifacts()
        built["orderbook_snapshots"][0][field] = True
        assert any(field in failure for failure in support.validation_failures(built))
