"""Pure-Python prediction-market formula implementations for PR162B."""

from __future__ import annotations


def _require_probability(value: float, name: str) -> float:
    result = float(value)
    if result < 0.0 or result > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def implied_probability_from_binary_price(price: float) -> float:
    return _require_probability(price, "price")


def fair_price_from_probability(probability: float) -> float:
    return _require_probability(probability, "probability")


def probability_edge(model_probability: float, market_probability: float) -> float:
    return _require_probability(model_probability, "model_probability") - _require_probability(
        market_probability,
        "market_probability",
    )


def expected_value_binary(p_win: float, profit_if_win: float, loss_if_lose: float) -> float:
    p = _require_probability(p_win, "p_win")
    return p * float(profit_if_win) - (1.0 - p) * float(loss_if_lose)


def fee_adjusted_expected_value(ev: float, fee: float) -> float:
    return float(ev) - float(fee)


def slippage_adjusted_expected_value(ev: float, slippage_cost: float) -> float:
    return float(ev) - float(slippage_cost)


def latency_adjusted_expected_value(ev: float, latency_penalty: float) -> float:
    return float(ev) - float(latency_penalty)


def expected_utility_candidate(expected_value: float, risk_penalty: float) -> float:
    return float(expected_value) - float(risk_penalty)


def binary_payoff_profit_loss(
    outcome: int,
    price_paid: float,
    payout_if_win: float = 1.0,
) -> float:
    if outcome not in (0, 1):
        raise ValueError("outcome must be 0 or 1")
    price = _require_probability(price_paid, "price_paid")
    payout = float(payout_if_win)
    return payout - price if outcome == 1 else -price


def break_even_probability(cost: float, profit_if_win: float, loss_if_lose: float) -> float:
    denominator = float(profit_if_win) + float(loss_if_lose)
    if denominator <= 0.0:
        raise ValueError("profit_if_win + loss_if_lose must be positive")
    return (float(loss_if_lose) + float(cost)) / denominator


def no_trade_zone_threshold(edge: float, threshold: float) -> bool:
    return abs(float(edge)) <= abs(float(threshold))


def no_trade_decision(edge: float, threshold: float) -> str:
    if no_trade_zone_threshold(edge, threshold):
        return "NO_TRADE"
    return "BUY_YES" if float(edge) > 0 else "BUY_NO"
