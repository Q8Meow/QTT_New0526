from ._helpers import assert_rows_have_contract, read_json


def test_no_orphan_report_and_routes() -> None:
    assert_rows_have_contract("value_route.jsonl")
    report = read_json("no_orphan.report.json")
    assert report["orphan_artifact_count"] == 0
    assert report["orphan_value_count"] == 0

