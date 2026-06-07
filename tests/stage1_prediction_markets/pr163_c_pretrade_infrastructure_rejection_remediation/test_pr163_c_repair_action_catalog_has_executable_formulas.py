from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.repair_formula_library import FORMULAS
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_repair_action_catalog_has_executable_formulas():
    rows = load_records("PR163_C_RepairActionCatalog.report.json")
    assert rows
    assert all(row["formula_ref"] in FORMULAS for row in rows)
    assert all(row["test_vector_ref"] for row in rows)
