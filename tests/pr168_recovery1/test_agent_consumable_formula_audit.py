from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_agent_consumable_formula_audit_keeps_source_and_formula_authority_candidate_only():
    assert_recovery1_valid()
    records = report("PR168_RECOVERY1_AgentConsumableFormulaAudit.report.json")["records"]

    assert records["agent_consumability_state"] == "REPLAY_PAPER_AGENT_CONSUMABLE_NON_PROOF_ONLY"
    assert records["agent_consumable_stack_evidence_count"] == 35
    assert records["agent_consumable_existing_formula_repair_count"] == 7
    assert records["agent_consumable_new_formula_count"] == 0
    assert records["agent_consumable_source_candidate_count"] == 5
    assert records["source_provenance_rows_are_source_truth_flag"] is False
    assert records["candidate_only_flag"] is True
    assert records["accepted_truth_flag"] is False
