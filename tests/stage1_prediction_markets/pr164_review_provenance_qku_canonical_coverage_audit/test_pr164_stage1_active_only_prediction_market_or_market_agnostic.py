from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records


def test_pr164_stage1_active_only_prediction_market_or_market_agnostic():
    rows = load_records("PR164_QKUStage1ActivationDormancyAudit.report.json")
    active = [row for row in rows if row["stage1_active_flag"]]

    assert active
    assert all(
        row["market_scope"].startswith(("PREDICTION_MARKET_", "MARKET_AGNOSTIC_"))
        for row in active
    )
