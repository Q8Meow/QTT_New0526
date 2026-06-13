from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_overfit_fdr_penalties_are_nonnegative():
    rows = assert_report_rows("PR166_SM2_OverfitFDRLedger.report.json", 3215)
    assert all(row["false_discovery_risk_adjustment"] >= 0 for row in rows[:100])
    assert all(row["overfit_risk_adjustment"] >= 0 for row in rows[:100])
