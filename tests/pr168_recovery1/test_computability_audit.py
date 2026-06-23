from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_computability_audit_classifies_improvements_as_stack_rows_not_formulas():
    assert_recovery1_valid()
    records = report("PR168_RECOVERY1_ComputabilityAudit.report.json")["records"]

    assert records["computability_audit_state"] == "COMPUTABLE_REPAIRED_RETESTED_STACK_ROWS_NON_PROOF"
    assert records["improved_non_proof_retest_stack_row_count"] == 35
    assert records["improved_rows_are_repaired_retested_stack_rows_flag"] is True
    assert records["improved_rows_are_new_formula_rows_flag"] is False
    assert records["new_formula_count"] == 0
    assert records["new_canonical_formula_id_count"] == 0
    assert records["expression_repair_count"] == 7
    assert records["expression_repairs_are_existing_formula_repairs_flag"] is True
