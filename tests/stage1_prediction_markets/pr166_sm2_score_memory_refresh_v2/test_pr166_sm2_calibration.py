from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_calibration_boost_receipts_have_units():
    rows = assert_report_rows("PR166_SM2_CalibrationLedger.report.json", 3215)
    assert all(0 <= row["calibration_score"] <= 1 for row in rows[:100])
    assert all(row["minimum_calibration_lift_needed"] >= 0 for row in rows[:100])
