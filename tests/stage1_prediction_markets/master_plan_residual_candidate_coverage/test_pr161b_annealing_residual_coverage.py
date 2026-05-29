from .pr161b_test_support import records, summary


def test_pr161b_annealing_residuals_are_classified_separately():
    assert summary()["annealing_residual_count"] > 0
    assert all(record["quantum_candidate_family"] == "ANNEALING" for record in records("annealing"))
