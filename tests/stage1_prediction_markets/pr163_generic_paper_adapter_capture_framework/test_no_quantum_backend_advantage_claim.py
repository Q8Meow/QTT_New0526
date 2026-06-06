def test_no_quantum_backend_advantage_claim(summary, records):
    rows = records("PR163_NoQuantumBackendAdvantageClaimAudit.report.json")
    assert rows[0]["quantum_backend_execution_count"] == 0
    assert rows[0]["quantum_simulator_execution_count"] == 0
    assert rows[0]["quantum_advantage_claim_count"] == 0
    assert summary["quantum_advantage_claim_count"] == 0
