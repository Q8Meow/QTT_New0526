from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_agent_task_queue_has_receipts():
    rows = assert_report_rows("PR166_S2_AgentTaskQueue.report.json", 3215)
    assert all(row["agent_task_receipt_status"] == "TASK_RECEIPT_CREATED_WITH_REPLAY_PAPER_OUTPUT" for row in rows[:100])
    assert all(row["source_agent_duty_ref"] for row in rows[:100])
