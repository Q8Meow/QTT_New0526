from .helpers import quantum_relevant


def test_pr159r_quantum_replay_paper_comparison_route_exists(pr159r_artifacts):
    assert all(record["replay_paper_quantum_comparison_required_flag"] is True for record in quantum_relevant(pr159r_artifacts["quantum"]["records"]))

