from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_agent_task_queue_has_receipts():
    rows = assert_report_rows("PR166_SM2_AgentTaskQueue.report.json", 8)
    assert all(row["task_receipt_status"] == "TASK_RECEIPT_CONNECTED" for row in rows)
