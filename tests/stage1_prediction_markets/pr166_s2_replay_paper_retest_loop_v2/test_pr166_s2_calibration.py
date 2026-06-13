from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_calibration_records_probability_inputs():
    row = assert_report_rows("PR166_S2_CalibrationLedger.report.json", 3215)[0]
    assert 0 <= row["model_probability_estimate"] <= 1
    assert 0 <= row["market_implied_probability"] <= 1
    assert row["calibration_bucket"]
