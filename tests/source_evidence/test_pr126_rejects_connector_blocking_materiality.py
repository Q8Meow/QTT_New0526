from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_connector_blocking_materiality():
    rejection = rejection_by_binding()["PR126_BINDING_CONNECTOR_BLOCKING"]

    assert rejection["implementation_gate_state"] == (
        "REJECTED_CONNECTOR_BLOCKING_MATERIALITY"
    )
    assert rejection["rejection_reason_code"] == "CONNECTOR_BLOCKING_MATERIALITY"
    assert rejection["network_io_allowed_flag"] is False
