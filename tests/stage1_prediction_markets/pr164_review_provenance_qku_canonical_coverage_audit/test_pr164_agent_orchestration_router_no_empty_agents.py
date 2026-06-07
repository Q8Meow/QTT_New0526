from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.agent_orchestration_router import AGENT_ROUTE_FIELDS
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_agent_orchestration_router_no_empty_agents():
    rows = load_records("PR164_AgentOrchestrationRouter.report.json")
    assert len(rows) == summary()["agent_orchestration_rows"]
    for row in rows[:500]:
        assert row["upstream_agent"]
        assert row["downstream_agent"]
        assert row["downstream_pr_route"]
        assert row["report_consumer"]
        assert all(row[field] for field in AGENT_ROUTE_FIELDS)
