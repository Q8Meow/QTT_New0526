import pytest

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.overfit_controls import (
    champion_challenger_score,
    false_discovery_penalty,
    lcb_from_mean_se,
    overfit_fdr_penalty,
    purged_window_overlap_check,
    sample_sufficiency_check,
    shrinkage_probability,
)


def test_false_discovery_penalty_increases_with_effective_trials():
    low = false_discovery_penalty(100, 5)
    high = false_discovery_penalty(100, 50)
    assert high > low


def test_overfit_penalty_lcb_and_shrinkage_probability():
    penalty = overfit_fdr_penalty(raw_edge=0.10, trial_count=100, effective_trial_count=20, confidence_penalty=2.0)
    assert penalty > 0
    assert lcb_from_mean_se(0.10, 0.02, 2.0) == pytest.approx(0.06)
    assert shrinkage_probability(0.80, 0.50, 0.25) == pytest.approx(0.575)


def test_champion_challenger_score_uses_ucb_style_exploration():
    explored = champion_challenger_score(0.10, 0.02, 2.0, total_trials=100, trials_i=4)
    well_sampled = champion_challenger_score(0.10, 0.02, 2.0, total_trials=100, trials_i=100)

    assert explored > well_sampled


def test_sample_and_purged_window_checks():
    assert sample_sufficiency_check(100, 50) is True
    assert sample_sufficiency_check(10, 50) is False
    assert purged_window_overlap_check((1, 10), (20, 30), label_horizon=5) is True
    assert purged_window_overlap_check((1, 10), (12, 30), label_horizon=5) is False
