import pytest

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.portfolio_utility import (
    crowding_adjusted_capacity,
    expected_shortfall_candidate,
    marginal_utility,
    risk_budget_check,
    robust_cluster_penalty,
    robust_covariance_or_hrp_cluster,
)


def test_marginal_utility_subtracts_risk_and_usage_terms():
    assert marginal_utility(1.0, 0.2, 0.1, 0.05, 0.03, 0.02) == pytest.approx(0.6)


def test_risk_budget_and_expected_shortfall():
    assert risk_budget_check(0.05, 0.10) is True
    assert risk_budget_check(0.15, 0.10) is False
    assert expected_shortfall_candidate([1, 2, 3, 10], alpha=0.75) == 10


def test_cluster_and_crowding_capacity_penalties():
    assert robust_cluster_penalty(0.35, 0.20) == pytest.approx(0.15)
    assert crowding_adjusted_capacity(40, capacity_limit=100, crowding_score=1.0) == pytest.approx(10)


def test_robust_covariance_or_hrp_cluster_outputs_shrinkage_and_weights():
    result = robust_covariance_or_hrp_cluster(
        sample_covariance=0.20,
        target_covariance=0.10,
        shrinkage=0.25,
        cluster_var_left=0.30,
        cluster_var_right=0.70,
    )

    assert result["shrunk_covariance"] == pytest.approx(0.175)
    assert result["hrp_left_weight"] == pytest.approx(0.70)
    assert result["hrp_right_weight"] == pytest.approx(0.30)
