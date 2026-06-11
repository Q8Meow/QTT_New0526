from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c


def test_score_component_provenance_covers_every_component(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_ScoreComponentProvenanceLedger.report.json"]
    ranking_count = len(pr165_d2_records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"])
    assert len(rows) == ranking_count * len(c.SCORE_WEIGHTS)
    first = rows[0]
    assert first["score_component_name"] in c.SCORE_WEIGHTS
    assert first["source_artifact_refs"]
