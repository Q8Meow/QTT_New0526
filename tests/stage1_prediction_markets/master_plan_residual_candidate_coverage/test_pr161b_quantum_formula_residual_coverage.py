from .pr161b_test_support import records, summary


def test_pr161b_quantum_formula_residuals_are_projected():
    assert summary()["quantum_formula_residual_count"] > 0
    assert records("quantum_formula")
