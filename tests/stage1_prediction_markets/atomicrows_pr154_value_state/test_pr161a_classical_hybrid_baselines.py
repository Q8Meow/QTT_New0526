from .pr161a_test_support import summary


def test_pr161a_classical_and_hybrid_baselines():
    assert summary()["classical_baseline_candidate_count"] == 4525
    assert summary()["hybrid_arbitration_candidate_count"] == 4525
    assert summary()["classical_baseline_required_count"] == 4525

