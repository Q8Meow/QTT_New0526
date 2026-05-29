from .pr161b_test_support import records, summary


def test_pr161b_formula_algorithm_residuals_are_counted():
    assert summary()["formula_residual_candidate_count"] > 0
    assert summary()["algorithm_residual_candidate_count"] >= 0
    assert records("formula_algorithm")
