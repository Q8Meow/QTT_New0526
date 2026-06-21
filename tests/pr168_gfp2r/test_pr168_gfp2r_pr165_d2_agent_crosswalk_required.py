from tests.pr168_gfp2r._helpers import records


def test_pr168_gfp2r_pr165_d2_agent_crosswalk_required() -> None:
    discovery = records("PR168_GFP2R_InputDiscovery")
    assert discovery["pr165_d2_agent_crosswalk_missing_refs"] == []
    routing = records("PR168_GFP2R_AgentRoutingAndNoOrphanProof")
    assert routing["agent_route_classes"]
    assert routing["no_orphan_violation_count"] == 0
