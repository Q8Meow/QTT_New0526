from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import rejection_by_case


def test_pr124_rejects_missing_unit_scale_scope_before_binding_creation():
    rejection = rejection_by_case("MISSING_UNIT_SCALE_SCOPE")

    assert rejection["readiness_state"] == "REJECTED_MISSING_UNIT_SCALE_SCOPE"
    assert rejection["blocker_codes"] == ["MISSING_UNIT_SCALE_SCOPE"]
    assert rejection["connector_semantic_binding_ledger_record_created"] is False
    assert rejection["production_connector_semantic_authority"] is False
