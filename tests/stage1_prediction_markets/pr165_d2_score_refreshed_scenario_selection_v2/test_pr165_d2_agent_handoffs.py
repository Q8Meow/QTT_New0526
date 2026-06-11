from __future__ import annotations


def test_agent_handoffs_generated_after_roster_audit(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_AgentSelectionHandoff.report.json"]
    assert rows
    assert all(row["handoff_generated_after_roster_audit_flag"] is True for row in rows)
    assert pr165_d2_records["PR165_D2_AgentTaskQueue.report.json"]
