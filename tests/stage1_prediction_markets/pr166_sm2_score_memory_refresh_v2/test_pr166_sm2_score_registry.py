from __future__ import annotations

from .helpers import assert_report_rows
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.score_refresh import score_memory_refresh_score_v2


def test_pr166_sm2_score_registry_formula_and_ranks():
    rows = assert_report_rows("PR166_SM2_ScoreRegistry.report.json", 3215)
    assert sorted(row["refreshed_rank"] for row in rows) == list(range(1, 3216))
    for row in rows[:25]:
        assert row["refreshed_score"] == score_memory_refresh_score_v2(row["score_formula_component_values"])
        assert row["profit_evidence_count"] == 0
