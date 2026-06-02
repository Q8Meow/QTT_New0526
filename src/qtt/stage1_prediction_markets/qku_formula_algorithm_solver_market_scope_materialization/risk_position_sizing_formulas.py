"""Position-sizing and risk formula implementations for PR162B."""

from __future__ import annotations

import math


def _values(values: list[float] | tuple[float, ...], name: str = "values") -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def kelly_fraction_binary(p_win: float, net_odds: float) -> float:
    p = float(p_win)
    b = float(net_odds)
    if p < 0.0 or p > 1.0:
        raise ValueError("p_win must be in [0, 1]")
    if b <= 0.0:
        raise ValueError("net_odds must be positive")
    q = 1.0 - p
    return (b * p - q) / b


def fractional_kelly(kelly_fraction: float, fraction: float) -> float:
    if fraction < 0.0 or fraction > 1.0:
        raise ValueError("fraction must be in [0, 1]")
    return float(kelly_fraction) * float(fraction)


def capped_position_size(raw_size: float, cap: float) -> float:
    cap_value = abs(float(cap))
    raw = float(raw_size)
    return max(-cap_value, min(raw, cap_value))


def capped_kelly(kelly_fraction: float, cap: float) -> float:
    return capped_position_size(kelly_fraction, cap)


def risk_budget_capped_position_size(raw_size: float, risk_budget: float, unit_risk: float) -> float:
    risk = abs(float(unit_risk))
    if risk <= 0.0:
        raise ValueError("unit_risk must be positive")
    budget_cap = abs(float(risk_budget)) / risk
    return capped_position_size(raw_size, budget_cap)


def max_exposure_cap(requested_exposure: float, max_exposure: float) -> float:
    return capped_position_size(requested_exposure, max_exposure)


def per_market_cap(requested_exposure: float, market_cap: float) -> float:
    return capped_position_size(requested_exposure, market_cap)


def per_event_cap(requested_exposure: float, event_cap: float) -> float:
    return capped_position_size(requested_exposure, event_cap)


def mean_return(values: list[float] | tuple[float, ...]) -> float:
    xs = _values(values)
    return sum(xs) / len(xs)


def variance(values: list[float] | tuple[float, ...]) -> float:
    xs = _values(values)
    mean = mean_return(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def covariance(x: list[float] | tuple[float, ...], y: list[float] | tuple[float, ...]) -> float:
    xs = _values(x, "x")
    ys = _values(y, "y")
    if len(xs) != len(ys):
        raise ValueError("x and y must have equal length")
    mx = mean_return(xs)
    my = mean_return(ys)
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=True)) / len(xs)


def correlation(x: list[float] | tuple[float, ...], y: list[float] | tuple[float, ...]) -> float:
    vx = variance(x)
    vy = variance(y)
    if vx <= 0.0 or vy <= 0.0:
        raise ValueError("variance must be positive for correlation")
    return covariance(x, y) / math.sqrt(vx * vy)


def volatility(returns: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(variance(returns))


def sharpe_ratio(portfolio_return: float, risk_free_rate: float, volatility: float) -> float:
    vol = float(volatility)
    if vol <= 0.0:
        raise ValueError("volatility must be positive")
    return (float(portfolio_return) - float(risk_free_rate)) / vol


def max_drawdown(equity_curve: list[float] | tuple[float, ...]) -> float:
    values = _values(equity_curve, "equity_curve")
    peak = values[0]
    worst = 0.0
    for value in values:
        if value > peak:
            peak = value
        if peak <= 0.0:
            raise ValueError("equity curve peak must be positive")
        worst = max(worst, (peak - value) / peak)
    return worst


def risk_adjusted_expected_value(expected_value: float, risk_penalty: float) -> float:
    return float(expected_value) - float(risk_penalty)
