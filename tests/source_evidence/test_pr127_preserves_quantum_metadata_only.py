from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    model_records,
)


def test_pr127_preserves_quantum_metadata_only():
    report = main_report()

    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    for model in model_records():
        metadata = model["quantum_forward_metadata_placeholder"]
        assert metadata["future_quantum_aware_latency_candidate_set_metadata_allowed"] is True
        assert metadata["quantum_backend_execution_count"] == 0
        assert metadata["quantum_advantage_claim_created"] is False
