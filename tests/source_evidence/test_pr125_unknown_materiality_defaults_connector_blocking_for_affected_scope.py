from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    snapshot,
)


def test_pr125_unknown_materiality_defaults_connector_blocking_for_affected_scope():
    event = materiality_by_event("EVENT_UNKNOWN_MATERIALITY_QUANTUM_DOC")
    snap = snapshot()

    assert event["declared_materiality_class"] == "UNKNOWN"
    assert event["materiality_class"] == "CONNECTOR_BLOCKING"
    assert event["unknown_materiality_defaulted_to_connector_blocking"] is True
    assert "PR125_BINDING_QUANTUM_PROVIDER_DOC_METADATA" in snap[
        "connector_binding_revalidation_required_ids"
    ]
