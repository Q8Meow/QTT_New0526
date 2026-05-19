from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import materiality_by_event


def test_pr125_info_only_materiality_keeps_binding_when_target_field_unchanged():
    event = materiality_by_event("EVENT_INFO_ONLY_GENERAL_DOC")

    assert event["materiality_class"] == "INFO_ONLY"
    assert event["target_field_delta_detected"] is False
    assert event["source_change_route"] == "RECORD_AND_KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED"
    assert event["connector_binding_revalidation_required"] is False
    assert event["connector_binding_revalidation_state"] == "KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED"
