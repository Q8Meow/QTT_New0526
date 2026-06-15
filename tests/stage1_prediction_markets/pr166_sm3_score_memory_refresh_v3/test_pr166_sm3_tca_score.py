from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_tca_score_report_contract():
    rows = assert_report_contract("PR166_SM3_TCAScore.report.json", 3215)
    assert rows
