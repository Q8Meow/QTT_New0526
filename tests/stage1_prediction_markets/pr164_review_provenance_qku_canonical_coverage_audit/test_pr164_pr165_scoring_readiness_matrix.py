from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_pr165_scoring_readiness_matrix():
    rows = load_records("PR164_PR165ScoringReadinessMatrix.report.json")
    record = summary()
    assert record["pr165_scoring_ready_rows"] + record["pr165_scoring_blocked_rows"] == len(rows)
    assert any(row["pr165_scoring_ready_flag"] for row in rows)
    assert any(row["pr165_scoring_blocked_flag"] for row in rows)
