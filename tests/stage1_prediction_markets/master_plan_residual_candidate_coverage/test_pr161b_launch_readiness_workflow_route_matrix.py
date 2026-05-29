from .pr161b_test_support import records, summary


def test_pr161b_launch_readiness_workflow_routes_cover_all_candidates():
    assert summary()["launch_readiness_workflow_route_count"] == len(records("launch_readiness_workflow"))
    assert all(record["live_use_allowed_flag"] is False for record in records("launch_readiness_workflow")[:25])
