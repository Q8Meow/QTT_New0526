from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_row_dag_report_contract():
    rows = assert_report_contract("PR166_SM3_RowDAG.report.json", 109)
    assert rows
