from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_agent_task_queue_report_contract():
    rows = assert_report_contract("PR166_SM3_AgentTaskQueue.report.json", 7)
    assert rows
