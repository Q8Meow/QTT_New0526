from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_qku_identity_reconciliation_no_orphans():
    rows = load_records("PR164_MasterQKUInventoryReconciliation.report.json")
    assert len(rows) == 9360
    assert all(row["qku_id"] for row in rows)
    assert summary()["all_orphan_counts_zero"] is True
