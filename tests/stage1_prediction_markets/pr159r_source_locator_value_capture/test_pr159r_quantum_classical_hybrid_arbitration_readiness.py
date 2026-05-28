from .helpers import quantum_relevant


def test_pr159r_quantum_classical_hybrid_arbitration_readiness(pr159r_artifacts):
    assert all(record["hybrid_optimizer_readiness_class"] for record in quantum_relevant(pr159r_artifacts["quantum"]["records"]))

