from .pr161b_test_support import records, summary


def test_pr161b_ising_residuals_are_classified_separately():
    assert summary()["ising_residual_count"] > 0
    assert all(record["quantum_candidate_family"] == "ISING" for record in records("ising"))
