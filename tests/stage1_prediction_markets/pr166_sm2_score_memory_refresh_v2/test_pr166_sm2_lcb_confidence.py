from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_lcb_and_confidence_are_recorded():
    lcb = assert_report_rows("PR166_SM2_EdgeLCBRegistry.report.json", 3215)
    confidence = assert_report_rows("PR166_SM2_ConfidenceRegistry.report.json", 3215)
    assert all(row["lcb_used_for_promotion"] for row in lcb[:100])
    assert all(0 <= row["result_confidence_score"] <= 1 for row in confidence[:100])
