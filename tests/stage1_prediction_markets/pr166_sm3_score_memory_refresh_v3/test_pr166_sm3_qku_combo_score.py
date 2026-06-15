from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_qku_combo_score_report_contract():
    rows = assert_report_contract("PR166_SM3_QKUComboScore.report.json", 3215)
    assert rows
