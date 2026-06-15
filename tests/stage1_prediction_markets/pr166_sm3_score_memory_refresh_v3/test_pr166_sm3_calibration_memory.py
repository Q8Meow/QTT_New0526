from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_calibration_memory_report_contract():
    rows = assert_report_contract("PR166_SM3_CalibrationMemory.report.json", 3215)
    assert rows
