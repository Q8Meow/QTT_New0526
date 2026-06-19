"""Prediction-market formula helpers for PR168-GFP."""

from __future__ import annotations

from collections.abc import Iterable


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def market_implied_probability(
    price: float,
    contract_terms: dict[str, float | str] | None = None,
    fee_adjustment: float = 0.0,
) -> float:
    """Return an adjusted probability from a normalized binary-contract price."""

    terms = contract_terms or {}
    multiplier = float(terms.get("price_multiplier", 1.0))
    normalized_price = float(price) / multiplier
    return clamp_probability(normalized_price + float(fee_adjustment))


def gross_edge(predicted_probability: float, market_implied_probability: float) -> float:
    return float(predicted_probability) - float(market_implied_probability)


def binary_contract_expected_value(
    win_probability: float,
    payout_if_win: float,
    loss_probability: float,
    stake: float,
) -> float:
    return float(win_probability) * float(payout_if_win) - float(loss_probability) * float(stake)


def expected_value(outcome_probabilities: Iterable[float], outcome_payoffs: Iterable[float]) -> float:
    return sum(float(p) * float(payoff) for p, payoff in zip(outcome_probabilities, outcome_payoffs))


def expected_value_from_edge(edge: float, position_size: float) -> float:
    return float(edge) * float(position_size)
