from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_agent_duty_ledger_uses_source_duty_refs():
    rows = assert_report_rows("PR166_S2_AgentDutyLedger.report.json", 3215)
    assert all(row["source_agent_duty_ref"] for row in rows[:100])
    assert all(row["reviewer_or_challenger_agent"] == "governance_agent" for row in rows[:100])
