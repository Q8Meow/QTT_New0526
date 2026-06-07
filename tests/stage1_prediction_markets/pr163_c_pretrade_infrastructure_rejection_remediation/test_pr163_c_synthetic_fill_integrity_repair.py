from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_synthetic_fill_integrity_repair():
    for row in load_records("PR163_C_SyntheticFillModelRepairRegistry.report.json"):
        assert row["fill_integrity_receipt_ref"]
        assert 0.05 <= row["fill_probability_candidate"] <= 0.99
        assert row["formula_ref"] == "PR163C_FORMULA::FILL_PROBABILITY"
