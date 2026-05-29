from .pr161b_test_support import records, summary


def test_pr161b_end_to_end_orchestration_record_count_matches_candidates():
    assert summary()["end_to_end_orchestration_record_count"] == len(records("orchestration_graph"))
    assert all(record["upstream_pr_ids"] and record["downstream_agent_roles"] for record in records("orchestration_graph")[:25])
