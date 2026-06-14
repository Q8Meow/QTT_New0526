from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_conversion_agent_queue_has_owner_and_reviewer():
    rows = assert_report_rows("PR166_SM2_ConversionAgentQueue.report.json", 3213)
    assert all(row["responsible_qtt_agent"] == row["owning_agent"] for row in rows[:100])
    assert all(row["reviewer_challenger_agent"] == "governance_agent" for row in rows[:100])
