from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import rejection_by_case


def test_pr124_rejects_venue_mismatch():
    rejection = rejection_by_case("VENUE_MISMATCH")

    assert rejection["readiness_state"] == "REJECTED_VENUE_MISMATCH"
    assert rejection["blocker_codes"] == ["VENUE_MISMATCH"]
    assert rejection["production_connector_semantic_authority"] is False
