from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit import constants as c


def test_pr162r_a_assigns_computability_class_to_every_candidate(summary, records):
    computability = records("PR162R_A_ComputabilityClassMatrix.report.json")
    assert len(computability) == summary["candidate_source_count"]
    assert summary["computability_class_missing_count"] == 0
    assert {row["computability_class"] for row in computability}.issubset(set(c.COMPUTABILITY_CLASSES))
    assert "METADATA_ONLY_NOT_READY" not in {row["computability_class"] for row in computability}
