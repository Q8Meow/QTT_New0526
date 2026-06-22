#!/usr/bin/env python3
"""Break-even and required-edge threshold formulas."""

from __future__ import annotations


def break_even_probability_after_costs(
    entry_price: float | None,
    candidate_cost_stack: float | None,
    payout_value: float = 1.0,
) -> float | None:
    if entry_price is None or candidate_cost_stack is None or payout_value <= 0:
        return None
    return round((float(entry_price) + float(candidate_cost_stack)) / float(payout_value), 6)


def required_probability_edge(
    break_even_probability: float | None,
    market_implied_probability: float | None,
) -> float | None:
    if break_even_probability is None or market_implied_probability is None:
        return None
    return round(float(break_even_probability) - float(market_implied_probability), 6)
