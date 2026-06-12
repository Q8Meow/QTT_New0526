from .conftest import assert_rows


def test_pr166_sf_agent_task_queue_has_required_agents(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_AgentRepairTaskQueue.report.json")
    agents = {row["agent_id"] for row in rows}
    assert {"research_agent", "parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent", "commander_agent", "governance_agent", "dashboard_agent"}.issubset(agents)
    assert all(row["expected_output"] for row in rows)
