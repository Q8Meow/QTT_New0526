from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_settlement_and_adverse_selection_are_recorded():
    settlement = assert_report_rows("PR166_S2_SettlementLedger.report.json", 3215)[0]
    adverse = assert_report_rows("PR166_S2_AdverseSelectionLedger.report.json", 3215)[0]
    assert settlement["settlement_assumption_ref"]
    assert adverse["adverse_selection_effect"] >= 0
