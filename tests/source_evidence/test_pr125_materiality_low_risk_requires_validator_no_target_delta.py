from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import materiality_by_event


def test_pr125_low_risk_materiality_keeps_binding_only_after_validator_no_delta():
    event = materiality_by_event("EVENT_LOW_RISK_GENERAL_DOC_VALIDATED")

    assert event["materiality_class"] == "LOW_RISK"
    assert event["validator_confirms_no_target_field_delta"] is True
    assert event["target_field_delta_detected"] is False
    assert event["revalidation_state"] == "REVALIDATED_NO_TARGET_FIELD_DELTA"
    assert event["connector_binding_revalidation_required"] is False
