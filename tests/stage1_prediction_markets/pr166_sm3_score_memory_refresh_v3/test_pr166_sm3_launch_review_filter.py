from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_launch_review_filter_report_contract():
    rows = assert_report_contract("PR166_SM3_LaunchReviewFilter.report.json", 150)
    assert rows
