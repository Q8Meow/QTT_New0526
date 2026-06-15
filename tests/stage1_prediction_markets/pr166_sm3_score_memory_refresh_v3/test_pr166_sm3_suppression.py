from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_suppression_report_contract():
    rows = assert_report_contract("PR166_SM3_SuppressionLedger.report.json", 2882)
    assert rows
