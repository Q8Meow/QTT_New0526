from __future__ import annotations


def test_row_count_reconciliation_records_exact_expected_counts(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_RowCountReconciliationLedger.report.json"]
    by_ref = {row["artifact_ref"]: row for row in rows}
    assert by_ref["PR166_SM_RefreshedScoreRegistry.report.json"]["actual_row_count"] == 3985
    assert by_ref["PR166_SM_QKUComputabilityClosureAudit.report.json"]["actual_row_count"] == 6502
    assert all(row["rows_not_invented_flag"] is True for row in rows)
