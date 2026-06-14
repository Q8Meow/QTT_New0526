from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_score_explain_rows_have_components():
    rows = assert_report_rows("PR166_SM2_ScoreExplainLedger.report.json", 3215)
    assert all(row["score_component_values"] for row in rows[:100])
    assert all(row["score_not_profit_evidence"] for row in rows[:100])
