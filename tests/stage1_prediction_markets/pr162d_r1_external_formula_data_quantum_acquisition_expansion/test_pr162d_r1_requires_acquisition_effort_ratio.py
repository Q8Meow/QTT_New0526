from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion import constants as c


def test_pr162d_r1_requires_acquisition_effort_ratio(summary):
    assert summary["acquisition_first_effort_ratio"] >= c.THRESHOLDS["acquisition_first_effort_ratio"]
