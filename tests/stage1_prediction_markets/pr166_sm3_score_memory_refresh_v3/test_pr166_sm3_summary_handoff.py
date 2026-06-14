from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_summary_handoff_report_contract():
    rows = assert_report_contract("PR166_SM3_SummaryHandoff.report.json", 1)
    assert rows
