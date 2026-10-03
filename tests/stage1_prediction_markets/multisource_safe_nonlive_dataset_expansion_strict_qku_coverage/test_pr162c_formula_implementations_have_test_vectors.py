from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.formula_test_vectors import execute_test_vector

from .test_support import records


def test_pr162c_formula_implementations_have_test_vectors(monkeypatch):
    formulas = records("PR162C_QKUFormulaRegistryDelta.report.json")
    algorithms = records("PR162C_QKUAlgorithmRegistryDelta.report.json")
    tests = records("PR162C_QKUFormulaTestVectorRegistryDelta.report.json")
    test_ids = {record["test_vector_id"] for record in tests}

    assert all(set(record["test_vector_refs"]) <= test_ids for record in formulas + algorithms)
    assert all(execute_test_vector(record) for record in tests)

    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import formula_test_vectors as native

    declared = native.formula_test_vector_delta_records() + native.algorithm_test_vector_delta_records()
    assert declared
    assert all(native.execute_test_vector(record) for record in declared)
    original = declared[0]
    invalid_pairs = (("json", "loads"),
        (original["implementation_module"], "__dict__"),
        (original["implementation_module"] + ".unselected", original["implementation_function"]),
        (None, original["implementation_function"]), ([], original["implementation_function"]),
        (original["implementation_module"], False))
    imports = []
    with monkeypatch.context() as patch:
        patch.setattr(native.importlib, "import_module", lambda name: imports.append(name))
        for module_name, function_name in invalid_pairs:
            record = dict(original, implementation_module=module_name, implementation_function=function_name)
            with pytest.raises(ValueError, match="callable is not declared"):
                native.execute_test_vector(record)
        assert imports == []
    with monkeypatch.context() as patch:
        def fail(**kwargs):
            raise RuntimeError("finite native target failure")
        patch.setattr(native.importlib, "import_module",
            lambda name: SimpleNamespace(**{original["implementation_function"]: fail}))
        with pytest.raises(RuntimeError, match="finite native target failure"):
            native.execute_test_vector(original)
