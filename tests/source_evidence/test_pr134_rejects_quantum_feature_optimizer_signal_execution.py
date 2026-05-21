from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_quantum_feature_optimizer_signal_execution():
    assert_malformed("malformed_quantum_runtime_feature_computation_created.v1.fixture.json", "QUANTUM_RUNTIME_FEATURE_COMPUTATION_CREATED")
    assert_malformed("malformed_quantum_optimizer_input_created.v1.fixture.json", "QUANTUM_OPTIMIZER_INPUT_CREATED")
    assert_malformed("malformed_quantum_trading_signal_created.v1.fixture.json", "QUANTUM_TRADING_SIGNAL_CREATED")
    payload = mutable_artifacts()
    payload["runtime_resolver_snapshots"][0]["quantum_execution_created"] = True
    assert "QUANTUM_EXECUTION_CREATED" in failure_codes(payload)
