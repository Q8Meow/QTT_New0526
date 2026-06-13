from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_settlement_and_adverse_ledgers_exist():
    settlement = assert_report_rows("PR166_SM2_SettlementLedger.report.json", 3215)
    adverse = assert_report_rows("PR166_SM2_AdverseSelection.report.json", 3215)
    assert all(row["settlement_drag"] >= 0 for row in settlement[:100])
    assert all(row["adverse_selection_ratio"] >= 0 for row in adverse[:100])
