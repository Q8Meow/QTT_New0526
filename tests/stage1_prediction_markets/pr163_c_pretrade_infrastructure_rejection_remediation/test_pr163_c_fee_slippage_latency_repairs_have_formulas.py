from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_fee_slippage_latency_repairs_have_formulas():
    assert all(row["formula_ref"] == "PR163C_FORMULA::FEE_COMPONENT" for row in load_records("PR163_C_FeeModelRepairRegistry.report.json"))
    assert all(row["formula_ref"] == "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS" for row in load_records("PR163_C_SlippageModelRepairRegistry.report.json"))
    assert all(row["formula_ref"] == "PR163C_FORMULA::LATENCY_STALE_DATA_COST" for row in load_records("PR163_C_LatencyModelRepairRegistry.report.json"))
