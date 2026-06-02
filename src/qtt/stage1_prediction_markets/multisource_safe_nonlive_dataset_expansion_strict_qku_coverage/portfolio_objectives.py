"""PR162C portfolio objective formula deltas."""

from __future__ import annotations


def correlation_penalized_portfolio_score(
    expected_return: float,
    average_pairwise_correlation: float,
    penalty_weight: float,
) -> float:
    return float(expected_return) - float(penalty_weight) * abs(float(average_pairwise_correlation))


def multi_objective_weighted_sum(values: list[float] | tuple[float, ...], weights: list[float] | tuple[float, ...]) -> float:
    xs = [float(value) for value in values]
    ws = [float(value) for value in weights]
    if not xs or len(xs) != len(ws):
        raise ValueError("values and weights must have equal non-zero length")
    return sum(value * weight for value, weight in zip(xs, ws, strict=True))
