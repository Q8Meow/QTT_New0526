from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    main_report,
    taxonomy_record,
)


def test_pr128_preserves_quantum_metadata_only():
    report = main_report()
    taxonomy = taxonomy_record()

    assert taxonomy["shared_scope_metadata_ids"] == ["PREDICTION_MARKETS_GENERAL"]
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
