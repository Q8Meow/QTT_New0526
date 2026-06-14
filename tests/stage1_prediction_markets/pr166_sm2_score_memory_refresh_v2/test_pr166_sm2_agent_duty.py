from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_agent_duty_uses_roster_sources():
    rows = assert_report_rows("PR166_SM2_AgentDutyLedger.report.json", 8)
    assert all("PR165_D2_AgentRosterDiscoveryAudit.report.json" in row["agent_duty_source_refs"] for row in rows)
