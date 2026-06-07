from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_does_not_force_pass_valid_rejections():
    assert summary()["valid_rejections_preserved"] == 1368
    assert summary()["valid_rejection_force_pass_count"] == 0
    assert {row["artificial_or_valid"] for row in load_records("PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json")} == {"ARTIFICIAL_INFRASTRUCTURE_REJECTION"}
