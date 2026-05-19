from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_stale_or_superseded_source_packet():
    rejections = rejection_by_binding()

    stale = rejections["PR126_BINDING_STALE_ACCEPTED_PACKET"]
    superseded = rejections["PR126_BINDING_SUPERSEDED_ACCEPTED_PACKET"]

    assert stale["implementation_gate_state"] == "REJECTED_STALE_ACCEPTED_PACKET"
    assert stale["rejection_reason_code"] == "ACCEPTED_PACKET_STALE"
    assert superseded["implementation_gate_state"] == "REJECTED_SUPERSEDED_ACCEPTED_PACKET"
    assert superseded["rejection_reason_code"] == "ACCEPTED_PACKET_SUPERSEDED"
