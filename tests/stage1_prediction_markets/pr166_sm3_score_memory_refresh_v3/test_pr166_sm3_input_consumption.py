from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_input_consumption_report_contract():
    rows = assert_report_contract("PR166_SM3_InputAudit.report.json", 96)
    assert rows
