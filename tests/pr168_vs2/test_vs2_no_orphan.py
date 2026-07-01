from .test_support import read_json, read_jsonl


def test_no_orphan_report_and_routes_cover_files() -> None:
    report = read_json("no_orphan.report.json")
    assert report["no_orphan_pass_flag"] is True
    assert report["orphan_artifact_count"] == 0
    assert read_jsonl("artifact_io.jsonl")
    assert read_jsonl("value_route.jsonl")


def test_agent_routes_reference_pr165_d2_sources() -> None:
    for row in read_jsonl("agent_alias_map.jsonl"):
        assert row["agent_roster_source_ref"].endswith("PR165_D2_AgentRosterDiscoveryAudit.report.json")
        assert row["agent_duty_crosswalk_ref"].endswith("PR165_D2_AgentDutySourceCrosswalk.report.json")
        assert row["invent_new_agent_authority_flag"] is False
