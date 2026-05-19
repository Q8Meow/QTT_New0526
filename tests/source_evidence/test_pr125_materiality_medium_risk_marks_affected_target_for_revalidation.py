from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    snapshot,
)


def test_pr125_medium_risk_marks_affected_target_for_revalidation():
    event = materiality_by_event("EVENT_MEDIUM_RISK_TARGET_DELTA")
    snap = snapshot()

    assert event["materiality_class"] == "MEDIUM_RISK"
    assert event["source_change_route"] == "REQUIRE_REVALIDATION_FOR_AFFECTED_TARGET_FIELD"
    assert event["connector_binding_revalidation_required"] is True
    assert "kalshi.fees.maker_fee_rule" in snap["no_new_binding_target_field_paths"]
