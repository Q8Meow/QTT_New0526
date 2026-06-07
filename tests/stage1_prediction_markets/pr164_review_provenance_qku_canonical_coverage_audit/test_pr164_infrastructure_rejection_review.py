from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_infrastructure_rejection_review():
    rows = load_records("PR164_PR163BInfrastructureRejectionReview.report.json")
    artificial = [row for row in rows if row["artificial_infrastructure_rejection_flag"]]

    assert len(rows) == summary()["pr163_b_rejection_rows_reviewed"]
    assert len(artificial) == summary()["pr163c_repair_trigger_rows"]
    assert all(row["downstream_pr_route"] == "ROUTE_TO_PR163_C_INFRA_REPAIR" for row in artificial)
