from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_pr165_d2_agent_crosswalk_required() -> None:
    roster = load("PR168_GFP2_AgentRosterDiscoveryAuditConsumption.report.json")
    duty = load("PR168_GFP2_AgentDutySourceCrosswalkConsumption.report.json")
    assert roster[0]["agent_ids"]
    assert duty[0]["agent_ids"]
