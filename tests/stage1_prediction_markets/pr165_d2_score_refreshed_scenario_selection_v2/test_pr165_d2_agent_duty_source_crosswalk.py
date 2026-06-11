from __future__ import annotations


def test_agent_duty_crosswalk_preserves_history(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_AgentDutySourceCrosswalk.report.json"]
    assert rows
    assert all(row["historical_duty_preserved_flag"] is True for row in rows)
    assert all(row["historical_duty_removed_flag"] is False for row in rows)
