from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import rejection_by_case


def test_pr124_rejects_target_field_mismatch():
    rejection = rejection_by_case("TARGET_FIELD_MISMATCH")

    assert rejection["readiness_state"] == "REJECTED_TARGET_FIELD_MISMATCH"
    assert rejection["blocker_codes"] == ["TARGET_FIELD_MISMATCH"]
    assert rejection["connector_semantic_binding_ledger_record_created"] is False
