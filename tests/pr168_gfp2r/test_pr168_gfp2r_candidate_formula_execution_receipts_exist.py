from tests.pr168_gfp2r._helpers import record_rows, rows


def test_pr168_gfp2r_candidate_formula_execution_receipts_exist() -> None:
    receipt_rows = record_rows("PR168_GFP2R_CandidateFormulaExecutionReceipts")
    executed = [row for row in rows("formula_execution") if row["formula_executed_flag"]]
    assert receipt_rows
    assert {row["compute_row_id"] for row in receipt_rows}.issubset({row["compute_row_id"] for row in executed})
