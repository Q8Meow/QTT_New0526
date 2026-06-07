from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_negative_memory_preparation():
    rows = load_records("PR164_PR165BNegativeMemoryPreparation.report.json")
    assert len(rows) == summary()["pr165b_negative_memory_preparation_rows"]
    assert all(row["condition_fingerprint"] for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)
