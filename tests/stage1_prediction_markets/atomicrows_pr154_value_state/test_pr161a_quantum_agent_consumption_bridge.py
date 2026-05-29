from .pr161a_test_support import records, summary


def test_pr161a_quantum_agent_consumption_bridge_maps_agents():
    bridge = records("quantum_agent_bridge")
    assert len(bridge) == summary()["quantum_candidates_mapped_to_downstream_qtt_agents_count"] == 41
    assert all("QTT_QUANTUM_ADVISORY_AGENT" in record["downstream_agent_roles"] for record in bridge)
    assert all(record["live_use_allowed_flag"] is False for record in bridge)

