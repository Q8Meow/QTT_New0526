from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_upstream_downstream_closure_matrix_no_orphans():
    rows = load_records("PR164_QKUUpstreamDownstreamClosureMatrix.report.json")
    assert rows
    assert all(row["no_orphan_state"] is True for row in rows)
    assert summary()["all_orphan_counts_zero"] is True
