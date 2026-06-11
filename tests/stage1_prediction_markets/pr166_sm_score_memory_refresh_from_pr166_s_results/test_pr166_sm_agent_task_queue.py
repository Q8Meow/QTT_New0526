def test_pr166_sm_agent_task_queue_covers_required_consumers(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_AgentTaskQueue.report.json"]
    agent_ids = {row["agent_id"] for row in rows}
    assert agent_ids == {
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
    }
    for row in rows:
        assert row["task_id"]
        assert row["task_type"]
        assert row["priority"] > 0
        assert row["urgency_bucket"]
        assert row["source_artifact_refs"]
        assert row["target_artifact_refs"]
        assert row["action"]
        assert row["expected_output"]
        assert row["downstream_pr_route"] in row["downstream_pr_refs"]
        assert row["validator_ref"].endswith("validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py")
