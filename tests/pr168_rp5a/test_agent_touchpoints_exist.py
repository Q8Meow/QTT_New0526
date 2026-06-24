from tests.pr168_rp5a._helpers import file_rows, load_report, load_rows


def test_agent_touchpoints_exist() -> None:
    rows = load_rows("agent_touchpoint_rows")
    report = load_report("PR168_RP5A_AgentCrosswalkTouchpoints.report.json")
    assert report["documented_equivalent_crosswalk_present"] is True
    assert {row["file_path"] for row in file_rows()} <= {row["file_path"] for row in rows}
