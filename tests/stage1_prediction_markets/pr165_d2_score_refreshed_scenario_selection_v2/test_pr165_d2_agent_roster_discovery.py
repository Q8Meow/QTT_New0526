from __future__ import annotations


def test_agent_roster_discovery_compiles_expected_agents(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]
    ids = {row["agent_id"] for row in rows}
    assert {"research_agent", "parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent", "commander_agent", "governance_agent", "dashboard_agent"}.issubset(ids)
    assert all(row["canonical_roster_source"] == "COMPILED_FROM_PRIOR_ARTIFACTS" for row in rows)
