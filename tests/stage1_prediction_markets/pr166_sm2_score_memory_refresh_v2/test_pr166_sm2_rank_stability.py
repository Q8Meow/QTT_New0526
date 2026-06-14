from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_rank_stability_rows_have_prior_and_refreshed_rank():
    rows = assert_report_rows("PR166_SM2_RankStabilityLedger.report.json", 3215)
    assert all(row["prior_rank"] >= 1 and row["refreshed_rank"] >= 1 for row in rows[:100])
