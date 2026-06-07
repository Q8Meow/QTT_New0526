from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records


def test_pr164_point_in_time_source_ledger_has_observed_at():
    rows = load_records("PR164_PointInTimeCandidateSourceLedger.report.json")
    assert rows
    assert all(row["observed_at_utc"] == "2026-06-06T00:00:00Z" for row in rows)
    assert all(row["candidate_value_not_source_truth"] is True for row in rows)
