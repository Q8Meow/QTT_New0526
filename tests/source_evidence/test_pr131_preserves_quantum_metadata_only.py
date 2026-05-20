from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_preserves_quantum_metadata_only():
    evidence = support.main_report()["PR131_QUANTUM_METADATA_ONLY_EVIDENCE"]

    assert evidence["quantum_execution_created"] is False
    assert evidence["quantum_backend_called"] is False
    assert evidence["quantum_simulator_called"] is False
    assert evidence["quantum_optimizer_called"] is False
    assert evidence["quantum_advantage_claim_created"] is False
    assert evidence["quantum_backend_simulator_optimizer_execution_count"] == 0
