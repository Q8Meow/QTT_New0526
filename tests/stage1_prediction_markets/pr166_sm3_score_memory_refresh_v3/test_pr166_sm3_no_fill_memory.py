from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_no_fill_memory_report_contract():
    rows = assert_report_contract("PR166_SM3_NoFillMemory.report.json", 183)
    assert rows
