from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.repair_formula_library import apply_formula
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_repair_formula_library_matches_test_vectors():
    for row in load_records("PR163_C_RepairTestVectorRegistry.report.json"):
        assert apply_formula(row["formula_ref"], row["inputs"]) == row["expected_output"]
        assert row["test_vector_passed"] is True
