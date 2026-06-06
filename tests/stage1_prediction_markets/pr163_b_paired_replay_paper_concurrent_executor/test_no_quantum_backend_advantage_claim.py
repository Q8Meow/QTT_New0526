def test_no_quantum_backend_advantage_claim(summary):
    assert summary["quantum_backend_execution_count"] == 0
    assert summary["quantum_simulator_execution_count"] == 0
    assert summary["quantum_advantage_claim_count"] == 0
