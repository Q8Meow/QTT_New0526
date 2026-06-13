from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_rank_aggregation_has_required_lenses():
    rows = assert_report_rows("PR166_SM2_RankAggregation.report.json", 3215)
    assert all("lcb_rank_lens_score" in row and "selection_readiness_score" in row for row in rows[:50])
