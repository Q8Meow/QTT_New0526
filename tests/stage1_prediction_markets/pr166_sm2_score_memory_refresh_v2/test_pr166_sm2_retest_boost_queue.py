from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_retest_boost_queue_requires_replay_paper():
    rows = assert_report_rows("PR166_SM2_RetestBoostQueue.report.json", 3213)
    assert all(row["replay_paper_retest_route"] for row in rows[:100])
    assert all(row["replay_paper_retest_required"] for row in rows[:100])
