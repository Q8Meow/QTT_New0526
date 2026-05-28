from .helpers import counts


def test_pr159r_all_quantum_relevant_targets_classified(pr159r_artifacts):
    receipt = counts(pr159r_artifacts)
    assert receipt["quantum_relevant_target_count"] == receipt["quantum_relevant_target_classified_count"]
    assert receipt["quantum_relevant_unclassified_count"] == 0

