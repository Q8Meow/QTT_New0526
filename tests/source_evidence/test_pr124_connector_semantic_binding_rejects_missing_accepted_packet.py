from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import rejection_by_case


def test_pr124_rejects_missing_accepted_packet():
    rejection = rejection_by_case("MISSING_ACCEPTED_PACKET")

    assert rejection["readiness_state"] == "REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE"
    assert rejection["blocker_codes"] == ["MISSING_ACCEPTED_SOURCE_EVIDENCE"]
    assert rejection["connector_semantic_binding_ledger_record_created"] is False
    assert rejection["production_connector_semantic_authority"] is False
