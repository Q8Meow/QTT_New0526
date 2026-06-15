from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_score_explain_report_contract():
    rows = assert_report_contract("PR166_SM3_ScoreExplain.report.json", 3215)
    assert rows
