from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_rejects_scope_or_venue_mismatch():
    artifacts = support.cloned_artifacts()
    artifacts["gate_report"]["private_state_read_requests"][0]["venue_id"] = (
        "PREDICTION_MARKETS_GENERAL"
    )

    failures = support.validation_failures(artifacts)

    assert any("three Stage-1 venues" in failure for failure in failures)
