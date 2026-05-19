from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_missing_accepted_evidence():
    rejection = rejection_by_binding()["PR126_BINDING_MISSING_ACCEPTED_SOURCE"]

    assert rejection["implementation_gate_state"] == (
        "REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE"
    )
    assert rejection["rejection_reason_code"] == "ACCEPTED_SOURCE_EVIDENCE_NOT_FOUND"
    assert rejection["accepted_source_fixture_authority_class"] is None
