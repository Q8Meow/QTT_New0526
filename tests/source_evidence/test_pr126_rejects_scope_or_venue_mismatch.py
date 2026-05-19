from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_scope_or_venue_mismatch():
    rejection = rejection_by_binding()["PR126_BINDING_SCOPE_OR_VENUE_MISMATCH"]

    assert rejection["implementation_gate_state"] == "REJECTED_SCOPE_OR_VENUE_MISMATCH"
    assert rejection["rejection_reason_code"] == "SCOPE_OR_VENUE_MISMATCH"
