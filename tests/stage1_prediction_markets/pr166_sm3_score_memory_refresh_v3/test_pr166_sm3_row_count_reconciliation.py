from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_row_count_reconciliation_report_contract():
    rows = assert_report_contract("PR166_SM3_RowCountLedger.report.json", 9)
    assert rows
