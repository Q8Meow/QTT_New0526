from .helpers import counts


def test_pr159r_no_quantum_backend_execution_or_advantage_claims(pr159r_artifacts):
    receipt = counts(pr159r_artifacts)
    assert receipt["quantum_backend_execution_count"] == 0
    assert receipt["quantum_advantage_profit_claim_count"] == 0

