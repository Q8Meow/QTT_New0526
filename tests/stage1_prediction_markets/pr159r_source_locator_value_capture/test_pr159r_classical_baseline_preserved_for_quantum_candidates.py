from .helpers import quantum_relevant


def test_pr159r_classical_baseline_preserved_for_quantum_candidates(pr159r_artifacts):
    assert all(record["classical_baseline_required_flag"] is True for record in quantum_relevant(pr159r_artifacts["quantum"]["records"]))

