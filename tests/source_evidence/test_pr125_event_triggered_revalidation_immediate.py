from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    schedule_by_packet,
)


def test_pr125_event_triggered_source_change_requires_immediate_control_plane_revalidation():
    record = schedule_by_packet("PR125_PACKET_KALSHI_ORDER_ENTRY_EVENT")
    event = materiality_by_event("EVENT_CONNECTOR_BLOCKING_ORDER_ENTRY")

    assert record["revalidation_state"] == "DUE_EVENT_TRIGGERED"
    assert record["revalidation_due_state"] == "DUE_EVENT_TRIGGERED"
    assert event["source_change_route"] == (
        "DOWNGRADE_AFFECTED_CONNECTOR_BINDING_TO_REVALIDATION_REQUIRED"
    )
    assert event["live_pretrade_use_allowed_flag"] is False
