from .pr161b_test_support import records, summary


def test_pr161b_parameter_range_residuals_are_counted():
    assert summary()["parameter_residual_candidate_count"] > 0
    assert summary()["parameter_range_residual_candidate_count"] > 0
    assert records("parameter_range")
