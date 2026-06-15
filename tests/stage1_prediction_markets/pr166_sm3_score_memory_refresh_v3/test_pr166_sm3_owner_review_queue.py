from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_owner_review_queue_report_contract():
    rows = assert_report_contract("PR166_SM3_OwnerReviewQueue.report.json", 75)
    assert rows
