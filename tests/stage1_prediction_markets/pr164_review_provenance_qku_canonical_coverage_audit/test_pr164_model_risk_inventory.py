from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_model_risk_inventory():
    rows = load_records("PR164_ModelRiskInventoryForQKU.report.json")
    assert len(rows) == summary()["model_risk_inventory_rows"]
    assert rows
    assert all(row["intended_use"] == "REPLAY_PAPER_CANDIDATE_ONLY_FOR_PR164" for row in rows)
    assert all(row["no_live_use_flag"] is True for row in rows)
