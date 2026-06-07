from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.central_reason_codes import MARKET_SCOPES
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_market_scope_classifier_uses_central_enums():
    rows = load_records("PR164_QKUMarketScopeCoverageAudit.report.json")
    assert len(rows) == summary()["qku_market_scope_rows"]
    assert all(row["market_scope"] in MARKET_SCOPES for row in rows)
    assert summary()["qku_unknown_market_scope_rows"] == 0
