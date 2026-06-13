from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_edge_lcb_and_confidence_are_bounded():
    lcb = assert_report_rows("PR166_S2_EdgeLCBRegistry.report.json", 3215)
    confidence = assert_report_rows("PR166_S2_ConfidenceRegistry.report.json", 3215)
    assert all(-1 <= row["edge_lower_confidence_bound"] <= 1 for row in lcb[:200])
    assert all(0 <= row["result_confidence_score"] <= 1 for row in confidence[:200])
