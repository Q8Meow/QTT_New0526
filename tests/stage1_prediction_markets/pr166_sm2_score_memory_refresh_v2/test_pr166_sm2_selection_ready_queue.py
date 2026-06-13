from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_selection_ready_queue_is_limited_to_true_positive_rows():
    assert_report_rows("PR166_SM2_SelectionReady.report.json", 2)
    assert_report_rows("PR166_SM2_NextSelectionQueue.report.json", 2)
    assert_report_rows("PR166_SM2_PR165D3Handoff.report.json", 2)
