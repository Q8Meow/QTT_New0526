from .pr161b_test_support import records, summary


def test_pr161b_vqe_residuals_are_classified_separately():
    assert summary()["vqe_residual_count"] > 0
    assert all(record["quantum_candidate_family"] == "VQE" for record in records("vqe"))
