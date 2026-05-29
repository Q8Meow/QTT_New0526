from .pr161a_test_support import records, summary


def test_pr161a_quantum_replay_paper_descriptors_exist_for_every_candidate():
    descriptors = records("quantum_replay_queue")
    assert len(descriptors) == summary()["quantum_replay_paper_experiment_descriptor_count"] == 41
    assert all(record["replay_lane_required_flag"] is True for record in descriptors)
    assert all(record["paper_lane_required_flag"] is True for record in descriptors)
    assert all(record["no_profit_evidence_created_flag"] is True for record in descriptors)

