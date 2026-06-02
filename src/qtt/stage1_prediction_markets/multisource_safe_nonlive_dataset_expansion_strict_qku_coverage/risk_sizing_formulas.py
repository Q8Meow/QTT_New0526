"""PR162C risk and sizing formula deltas."""

from __future__ import annotations


def drawdown_capped_kelly(kelly_fraction: float, max_fraction: float, drawdown: float, max_drawdown: float) -> float:
    if max_fraction < 0.0:
        raise ValueError("max_fraction must be non-negative")
    if drawdown < 0.0 or max_drawdown <= 0.0:
        raise ValueError("drawdown must be non-negative and max_drawdown positive")
    drawdown_scale = max(0.0, 1.0 - float(drawdown) / float(max_drawdown))
    raw = float(kelly_fraction) * drawdown_scale
    cap = abs(float(max_fraction))
    return max(-cap, min(raw, cap))


def liquidity_adjusted_size(raw_size: float, available_liquidity: float, liquidity_fraction_cap: float) -> float:
    if available_liquidity < 0.0 or liquidity_fraction_cap < 0.0:
        raise ValueError("liquidity inputs must be non-negative")
    cap = float(available_liquidity) * float(liquidity_fraction_cap)
    return max(-cap, min(float(raw_size), cap))


def max_position_by_budget(budget: float, price: float) -> float:
    if budget < 0.0:
        raise ValueError("budget must be non-negative")
    if price <= 0.0:
        raise ValueError("price must be positive")
    return float(budget) / float(price)


def drawdown_penalized_score(score: float, drawdown: float, penalty_weight: float) -> float:
    if drawdown < 0.0:
        raise ValueError("drawdown must be non-negative")
    return float(score) - float(penalty_weight) * float(drawdown)
