from __future__ import annotations

from ._helpers import load_report, load_rows


def test_rp5c_agent_duty_inputs_are_consumed_or_blocked() -> None:
    report = load_report("PR168_RP5C_AgentDutyInput.report.json")
    groups = load_rows("agent_responsibility_group_registry")

    assert report["roster_exists"] is True
    assert report["duty_crosswalk_exists"] is True
    assert report["parsed_agent_count"] > 0
    assert report["missing_blocker_codes"] == []
    assert groups
    assert all("group_authority_class" in row for row in groups)
    assert any(row["canonical_agent_refs"] for row in groups)
