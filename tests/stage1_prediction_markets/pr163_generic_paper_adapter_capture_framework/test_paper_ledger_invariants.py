def test_ledger_invariant_audit_has_zero_violations(records, summary):
    rows = records("PR163_PaperLedgerInvariantAudit.report.json")
    assert rows
    assert sum(row["violation_count"] for row in rows) == summary["ledger_invariant_violation_count"] == 0
