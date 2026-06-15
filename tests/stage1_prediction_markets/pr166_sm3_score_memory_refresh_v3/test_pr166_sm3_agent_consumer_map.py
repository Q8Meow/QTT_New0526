from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_agent_consumer_map_report_contract():
    rows = assert_report_contract("PR166_SM3_AgentConsumerMap.report.json", 109)
    assert rows
