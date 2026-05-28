from .helpers import quantum_relevant


def test_pr159r_quantum_compatibility_targets_prioritized(pr159r_artifacts):
    relevant = quantum_relevant(pr159r_artifacts["quantum"]["records"])
    assert relevant
    assert all(record["quantum_priority_candidate_flag"] is True for record in relevant)

