from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_agent_orchestration_no_orphans():
    rows = load_records("PR163_C_AgentRepairOrchestrationRouter.report.json")
    assert len(rows) == summary()["agent_orchestration_route_rows"]
    assert all(row["upstream_agent"] and row["downstream_agent"] and row["report_consumer"] for row in rows)
    assert summary()["orphan_qku_count"] == summary()["orphan_pr_file_count"] == summary()["dead_end_file_count"] == 0
