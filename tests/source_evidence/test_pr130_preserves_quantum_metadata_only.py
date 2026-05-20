from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_quantum_metadata_only():
    report = support.main_report()

    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
