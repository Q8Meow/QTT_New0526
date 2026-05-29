from .pr161b_test_support import records, summary


def test_pr161b_qaoa_residuals_are_classified_separately():
    assert summary()["qaoa_residual_count"] > 0
    assert all(record["quantum_candidate_family"] == "QAOA" for record in records("qaoa"))
