from .pr161b_test_support import quantum_records, summary


def test_pr161b_quantum_optimizer_residuals_have_required_routes():
    assert summary()["quantum_residual_candidate_count"] > 0
    for record in quantum_records()[:25]:
        assert record["classical_baseline_required_flag"] is True
        assert record["hybrid_arbitration_required_flag"] is True
        assert record["replay_paper_required_flag"] is True
        assert record["downstream_pr87_pr92_route"]
