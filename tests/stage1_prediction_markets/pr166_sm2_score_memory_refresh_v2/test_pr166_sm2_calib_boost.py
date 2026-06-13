from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_calibration_boost_ledger_has_lift():
    rows = assert_report_rows("PR166_SM2_CalibBoostLedger.report.json", 3213)
    assert all(row["minimum_calibration_lift_needed"] >= 0 for row in rows[:100])
