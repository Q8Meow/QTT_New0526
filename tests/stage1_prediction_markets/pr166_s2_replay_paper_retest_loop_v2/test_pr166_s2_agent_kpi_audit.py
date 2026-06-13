from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_agent_kpi_audit_covers_roster():
    rows = assert_report_rows("PR166_S2_AgentKPIAudit.report.json", summary()["agent_kpi_audit_rows"])
    assert len({row["agent_id"] for row in rows}) == 8
    assert all(row["next_action_quality"] == "ACTIONABLE_REPLAY_PAPER_ROUTE_RECEIPT" for row in rows)
