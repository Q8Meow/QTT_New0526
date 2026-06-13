from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_threshold_policy_records_derivation():
    rows = assert_report_rows("PR166_S2_ThresholdPolicy.report.json", 5)
    assert all(row["derivation_method"] for row in rows)
    assert all(row["replay_paper_only_boundary"] is True for row in rows)
