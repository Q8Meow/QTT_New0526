from .pr161b_test_support import records, summary


def test_pr161b_owner_dashboard_review_routes_are_recorded():
    assert summary()["owner_dashboard_review_route_count"] == len(records("owner_dashboard"))
    assert records("owner_dashboard")
