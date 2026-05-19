from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import rejection_by_case


def test_pr124_rejects_stale_or_conflicted_accepted_packet():
    rejection = rejection_by_case("STALE_OR_CONFLICTED_ACCEPTED_PACKET")

    assert rejection["readiness_state"] == "REJECTED_STALE_OR_CONFLICTED_ACCEPTED_PACKET"
    assert rejection["blocker_codes"] == ["STALE_OR_CONFLICTED_ACCEPTED_PACKET"]
    assert rejection["connector_semantic_binding_ledger_record_created"] is False
