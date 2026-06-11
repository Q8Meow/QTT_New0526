from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.report_writer import (
    candidate_selection_score,
    numeric,
)


def test_ranking_score_formula_and_selection_gate(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]
    assert len(rows) == 3985
    first = rows[0]
    assert abs(candidate_selection_score({field: numeric(first, field) for field in c.SCORE_WEIGHTS}) - first["candidate_selection_score_v2"]) < 0.00001
    selected = [row for row in rows if row["selected_for_retest_v2_flag"]]
    assert selected
    assert all(row["net_edge_after_costs"] >= c.MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD for row in selected)
