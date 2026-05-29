from .pr161b_test_support import summary


def test_pr161b_hybrid_quantum_classical_residual_count_is_present():
    assert summary()["hybrid_quantum_classical_residual_count"] >= 0
