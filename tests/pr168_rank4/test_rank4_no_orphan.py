from ._helpers import report, rows


def test_no_orphan_routes_cover_artifacts() -> None:
    assert report("no_orphan.report.json")["orphan_artifact_count"] == 0
    assert report("no_orphan.report.json")["orphan_value_count"] == 0
    assert rows("artifact_io.jsonl")
    assert rows("rank_user_conn_route.jsonl")

