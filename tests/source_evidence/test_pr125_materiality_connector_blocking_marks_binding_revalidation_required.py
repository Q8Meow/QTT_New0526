from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    snapshot,
)


def test_pr125_connector_blocking_marks_binding_revalidation_required():
    event = materiality_by_event("EVENT_CONNECTOR_BLOCKING_ORDER_ENTRY")
    snap = snapshot()

    assert event["materiality_class"] == "CONNECTOR_BLOCKING"
    assert event["connector_binding_revalidation_required"] is True
    assert event["connector_binding_revalidation_state"] == "SOURCE_REVALIDATION_REQUIRED"
    assert "PR125_BINDING_KALSHI_ORDER_ENTRY" in snap[
        "connector_binding_revalidation_required_ids"
    ]
