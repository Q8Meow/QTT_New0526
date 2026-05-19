from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_revalidation_required_binding():
    rejection = rejection_by_binding()["PR126_BINDING_REVALIDATION_REQUIRED"]

    assert rejection["implementation_gate_state"] == "REJECTED_REVALIDATION_REQUIRED"
    assert rejection["connector_binding_revalidation_state"] == "REVALIDATION_REQUIRED"
    assert rejection["rejection_reason_code"] == "CONNECTOR_BINDING_REVALIDATION_REQUIRED"
