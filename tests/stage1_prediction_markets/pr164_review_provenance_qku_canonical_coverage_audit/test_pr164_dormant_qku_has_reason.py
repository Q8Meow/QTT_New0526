from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_dormant_qku_has_reason():
    rows = load_records("PR164_QKUStage1ActivationDormancyAudit.report.json")
    dormant = [row for row in rows if row["dormant_flag"]]

    assert len(dormant) == summary()["qku_dormant_rows"]
    assert dormant
    assert all(row["dormant_reason"] for row in dormant)
