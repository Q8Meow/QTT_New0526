from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.central_reason_codes import DIVERGENCE_MATERIALITY
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_divergence_materiality():
    rows = load_records("PR164_PR163BDivergenceMaterialityReview.report.json")
    assert len(rows) == summary()["pr163_b_divergence_rows_reviewed"]
    assert all(row["divergence_materiality"] in DIVERGENCE_MATERIALITY for row in rows)
