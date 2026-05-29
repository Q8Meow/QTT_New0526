from .pr161b_test_support import records, summary


def test_pr161b_replay_paper_workflow_routes_do_not_create_results():
    assert summary()["replay_paper_workflow_route_count"] == len(records("replay_paper_workflow"))
    assert all(record["profit_evidence_created_flag"] is False for record in records("replay_paper_workflow")[:25])
