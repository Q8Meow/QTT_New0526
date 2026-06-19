"""Portfolio and risk utility formulas for PR168-GFP."""

from __future__ import annotations


def marginal_utility(
    edge_contribution: float,
    risk_contribution: float,
    capital_usage: float,
    correlation_penalty: float,
    liquidity_usage: float,
    capacity_usage: float,
) -> float:
    return (
        float(edge_contribution)
        - float(risk_contribution)
        - float(capital_usage)
        - float(correlation_penalty)
        - float(liquidity_usage)
        - float(capacity_usage)
    )


def diversification_penalty(correlation_cluster_exposure: float, common_driver_exposure: float) -> float:
    return max(0.0, float(correlation_cluster_exposure)) + max(0.0, float(common_driver_exposure))


def risk_budget_check(candidate_risk: float, available_risk_budget: float) -> bool:
    return float(candidate_risk) <= float(available_risk_budget)


def expected_shortfall_candidate(loss_distribution: list[float], alpha: float) -> float:
    if not loss_distribution:
        raise ValueError("loss_distribution must not be empty")
    tail_fraction = max(0.0, min(1.0, 1.0 - float(alpha)))
    sorted_losses = sorted(float(loss) for loss in loss_distribution)
    tail_count = max(1, int(round(len(sorted_losses) * tail_fraction)))
    tail = sorted_losses[-tail_count:]
    return sum(tail) / len(tail)


def drawdown_contribution(candidate_return_path: list[float], portfolio_return_path: list[float]) -> float:
    combined = [float(c) + float(p) for c, p in zip(candidate_return_path, portfolio_return_path)]
    peak = float("-inf")
    max_drawdown = 0.0
    for value in combined:
        peak = max(peak, value)
        max_drawdown = max(max_drawdown, peak - value)
    return max_drawdown


def robust_cluster_penalty(cluster_exposure: float, concentration_limit: float) -> float:
    return max(float(cluster_exposure) - float(concentration_limit), 0.0)


def robust_covariance_or_hrp_cluster(
    sample_covariance: float,
    target_covariance: float,
    shrinkage: float,
    cluster_var_left: float,
    cluster_var_right: float,
) -> dict[str, float]:
    weight = max(0.0, min(1.0, float(shrinkage)))
    shrunk_covariance = weight * float(target_covariance) + (1.0 - weight) * float(sample_covariance)
    total_cluster_var = max(float(cluster_var_left) + float(cluster_var_right), 1e-12)
    hrp_left_weight = 1.0 - float(cluster_var_left) / total_cluster_var
    return {
        "shrunk_covariance": shrunk_covariance,
        "hrp_left_weight": hrp_left_weight,
        "hrp_right_weight": 1.0 - hrp_left_weight,
    }


def crowding_adjusted_capacity(quantity: float, capacity_limit: float, crowding_score: float) -> float:
    return float(capacity_limit) / (1.0 + max(float(crowding_score), 0.0)) - float(quantity)
