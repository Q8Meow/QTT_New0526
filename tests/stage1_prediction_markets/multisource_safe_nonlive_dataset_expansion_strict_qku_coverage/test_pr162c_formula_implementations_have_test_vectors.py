from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.formula_test_vectors import execute_test_vector

from .test_support import records


def test_pr162c_formula_implementations_have_test_vectors():
    formulas = records("PR162C_QKUFormulaRegistryDelta.report.json")
    algorithms = records("PR162C_QKUAlgorithmRegistryDelta.report.json")
    tests = records("PR162C_QKUFormulaTestVectorRegistryDelta.report.json")
    test_ids = {record["test_vector_id"] for record in tests}

    assert all(set(record["test_vector_refs"]) <= test_ids for record in formulas + algorithms)
    assert all(execute_test_vector(record) for record in tests)
