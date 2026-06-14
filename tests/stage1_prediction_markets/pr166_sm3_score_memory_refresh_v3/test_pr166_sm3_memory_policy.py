from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_memory_policy_report_contract():
    rows = assert_report_contract("PR166_SM3_MemoryPolicy.report.json", 6)
    assert rows
