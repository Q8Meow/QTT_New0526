from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_missing_unit_scale_scope():
    rejection = rejection_by_binding()["PR126_BINDING_MISSING_UNIT_SCALE_SCOPE"]

    assert rejection["implementation_gate_state"] == "REJECTED_MISSING_UNIT_SCALE_SCOPE"
    assert rejection["rejection_reason_code"] == "MISSING_UNIT_SCALE_OR_SCOPE"
