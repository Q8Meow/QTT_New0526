from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_rank_delta_covers_scores():
    rows = assert_report_rows("PR166_SM2_RankDeltaRegistry.report.json", 3215)
    assert all("rank_delta" in row for row in rows)
