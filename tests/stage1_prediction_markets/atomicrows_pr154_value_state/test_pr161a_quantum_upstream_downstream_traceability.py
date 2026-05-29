from .pr161a_test_support import records, summary


def test_pr161a_quantum_upstream_downstream_traceability_populated():
    trace = records("quantum_traceability")
    assert len(trace) == summary()["quantum_candidates_mapped_to_pr82_pr86_count"] == 41
    assert all({"PR82", "PR83", "PR84", "PR85", "PR86"}.issubset(set(record["upstream_pr_labels_consumed"])) for record in trace)
    assert all("PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION" in record["downstream_pr_targets"] for record in trace)

