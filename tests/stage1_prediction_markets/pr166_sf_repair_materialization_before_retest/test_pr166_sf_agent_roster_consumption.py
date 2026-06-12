from .conftest import assert_rows


def test_pr166_sf_consumes_pr165_d2_agent_roster_without_expansion(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_AgentRosterAudit.report.json")
    assert len(rows) == 8
    assert all(row["new_agent_created_in_this_pr_flag"] is False for row in rows)
    assert {row["agent_id"] for row in rows} >= {"research_agent", "parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent"}
