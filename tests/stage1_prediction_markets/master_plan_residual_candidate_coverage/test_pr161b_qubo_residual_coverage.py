from .pr161b_test_support import records, summary


def test_pr161b_qubo_residuals_are_classified_separately():
    assert summary()["qubo_residual_count"] > 0
    assert all(record["quantum_candidate_family"] == "QUBO" for record in records("qubo"))
