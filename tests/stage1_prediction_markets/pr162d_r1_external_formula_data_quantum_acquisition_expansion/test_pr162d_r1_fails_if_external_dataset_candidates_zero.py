from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion.validator import _validate_summary_thresholds


def test_pr162d_r1_fails_if_external_dataset_candidates_zero(summary):
    bad = dict(summary, external_dataset_candidates_created=0)
    failures: list[str] = []
    _validate_summary_thresholds(bad, failures)
    assert any("external_dataset_candidates_created" in failure for failure in failures)
