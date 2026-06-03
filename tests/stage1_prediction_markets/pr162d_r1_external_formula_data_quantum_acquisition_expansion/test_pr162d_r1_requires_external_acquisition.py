from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion import constants as c


def test_pr162d_r1_requires_external_acquisition(summary):
    assert summary["external_sources_scouted_count"] >= c.THRESHOLDS["external_sources_scouted_count"]
    assert summary["external_source_candidates_created"] >= c.THRESHOLDS["external_source_candidates_created"]
