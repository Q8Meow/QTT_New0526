from .helpers import counts


def test_pr159r_quantum_forward_optimizer_readiness_created(pr159r_artifacts):
    assert pr159r_artifacts["quantum"]["record_count"] == 869
    assert counts(pr159r_artifacts)["quantum_forward_optimizer_readiness_update_count"] == 869
