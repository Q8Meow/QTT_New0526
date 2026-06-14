from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_diversity_limits_near_duplicates():
    rows = assert_report_rows("PR166_SM2_DiversityLedger.report.json", 3215)
    assert all(row["near_duplicate_cluster_limit_applied"] for row in rows[:100])
