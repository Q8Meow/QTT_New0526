from .pr161b_test_support import records, summary


def test_pr161b_replay_paper_routes_exist_for_testable_candidates():
    assert summary()["replay_paper_residual_candidate_count"] == len(records("replay_paper_workflow"))
    assert all(record["replay_execution_performed_flag"] is False for record in records("replay_paper_workflow")[:25])
