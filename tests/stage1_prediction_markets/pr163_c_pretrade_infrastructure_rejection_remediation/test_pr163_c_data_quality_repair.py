from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_data_quality_repair():
    rows = load_records("PR163_C_DataQualityRepairRegistry.report.json")
    assert all(row["exact_defect_fields"] for row in rows)
    assert all(row["unit_mismatch_state"] == "NORMALIZED_TO_PROBABILITY_PRICE" for row in rows)
