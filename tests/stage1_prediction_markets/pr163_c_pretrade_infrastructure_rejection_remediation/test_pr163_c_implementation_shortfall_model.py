from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_implementation_shortfall_model():
    rows = load_records("PR163_C_ImplementationShortfallModelRegistry.report.json")
    assert all(row["formula_ref"] == "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL" for row in rows)
    assert all("implementation_shortfall_candidate" in row for row in rows)
