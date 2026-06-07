from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import summary


def test_pr164_reviews_every_pr163_b_evidence_row():
    record = summary()
    assert record["pr163_b_evidence_rows_reviewed"] == 6502
    assert record["pr163_b_divergence_rows_reviewed"] == 6502
    assert record["pr163_b_tca_rows_reviewed"] == 6502
    assert record["pr163_b_rejection_rows_reviewed"] == 6502
