from .helpers import quantum_relevant


def test_pr159r_pr169_route_for_true_quantum_backend_candidates(pr159r_artifacts):
    assert all(record["future_PR169_quantum_backend_gated_sandbox_route"] == "PR169_QUANTUM_BACKEND_GATED_SANDBOX" for record in quantum_relevant(pr159r_artifacts["quantum"]["records"]))

