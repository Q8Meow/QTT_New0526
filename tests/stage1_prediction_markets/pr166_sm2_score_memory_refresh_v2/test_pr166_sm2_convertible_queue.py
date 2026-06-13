from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_convertible_queue_covers_all_negatives():
    rows = assert_report_rows("PR166_SM2_ConvertibleQueue.report.json", 3213)
    assert all(row["replay_paper_retest_required"] for row in rows[:100])
