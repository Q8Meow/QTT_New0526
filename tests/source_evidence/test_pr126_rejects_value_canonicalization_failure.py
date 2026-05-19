from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_value_canonicalization_failure():
    rejection = rejection_by_binding()["PR126_BINDING_CANONICALIZATION_FAILURE"]

    assert rejection["implementation_gate_state"] == "REJECTED_CANONICALIZATION_FAILURE"
    assert rejection["rejection_reason_code"] == (
        "CANONICALIZATION_MEANING_NOT_PRESERVED"
    )
