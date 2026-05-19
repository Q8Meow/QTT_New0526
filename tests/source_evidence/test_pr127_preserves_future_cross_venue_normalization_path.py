from tests.source_evidence.pr127_execution_lifecycle_support import (
    handoff,
    main_report,
    model_records,
)


def test_pr127_preserves_future_cross_venue_normalization_path():
    report = main_report()
    manifest = handoff()

    assert report["future_cross_venue_normalization_path_preserved"] is True
    assert manifest["future_cross_venue_normalization_path_preserved"] is True
    assert manifest["required_future_normalization_dimensions"] == [
        "execution_phase_taxonomy",
        "execution_transition_taxonomy",
        "fill_integrity_taxonomy",
        "cashflow_pnl_taxonomy",
        "latency_component_taxonomy",
        "settlement_finality_taxonomy",
        "reconciliation_taxonomy",
        "order_state_taxonomy",
        "cancellation_state_taxonomy",
        "partial_fill_state_taxonomy",
        "rejection_error_taxonomy",
    ]
    for model in model_records():
        assert model["future_cross_venue_normalization_path_preserved"] is True
