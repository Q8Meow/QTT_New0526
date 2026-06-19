"""Execution cost formulas used by PR168-GFP validators and reports."""

from __future__ import annotations

import math


def _side_sign(side: str) -> int:
    normalized = side.strip().lower()
    if normalized in {"buy", "yes_buy", "long"}:
        return 1
    if normalized in {"sell", "yes_sell", "short"}:
        return -1
    raise ValueError(f"unsupported side: {side!r}")


def spread_cost(bid: float, ask: float, side: str, quantity: float) -> float:
    mid = (float(bid) + float(ask)) / 2.0
    decision_price = float(ask) if _side_sign(side) > 0 else float(bid)
    return abs(decision_price - mid) * float(quantity)


def explicit_fee_cost(fee_rate: float, notional: float, fixed_fee: float = 0.0) -> float:
    return float(fee_rate) * float(notional) + float(fixed_fee)


def slippage_cost(expected_price: float, fill_price: float, side: str, quantity: float) -> float:
    signed_difference = _side_sign(side) * (float(fill_price) - float(expected_price))
    return max(signed_difference, 0.0) * float(quantity)


def market_impact_penalty(quantity: float, visible_depth: float, impact_coefficient: float) -> float:
    depth = max(float(visible_depth), 1e-12)
    qty = max(float(quantity), 0.0)
    return float(impact_coefficient) * qty * math.sqrt(qty / depth)


def adverse_selection_penalty(
    probability_move_against: float,
    adverse_move_size: float,
    quantity: float,
) -> float:
    return float(probability_move_against) * float(adverse_move_size) * float(quantity)


def implementation_shortfall(
    decision_price: float,
    execution_price: float,
    side: str,
    quantity: float,
    fees: float,
    opportunity_cost: float = 0.0,
) -> float:
    return _side_sign(side) * (float(execution_price) - float(decision_price)) * float(quantity) + float(fees) + float(opportunity_cost)


def latency_decay(edge: float, latency_ms: float, half_life_ms: float) -> float:
    half_life = max(float(half_life_ms), 1e-12)
    return float(edge) * (1.0 - 2.0 ** (-float(latency_ms) / half_life))


def queue_nonfill_penalty(edge: float, fill_probability: float) -> float:
    return abs(float(edge)) * (1.0 - max(0.0, min(1.0, float(fill_probability))))


def partial_fill_penalty(edge: float, requested_quantity: float, filled_quantity: float) -> float:
    requested = max(float(requested_quantity), 1e-12)
    fill_ratio = max(0.0, min(1.0, float(filled_quantity) / requested))
    return abs(float(edge)) * (1.0 - fill_ratio)


def capacity_crowding_penalty(quantity: float, capacity_limit: float, crowding_coefficient: float) -> float:
    capacity = max(float(capacity_limit), 1e-12)
    excess_ratio = max(float(quantity) / capacity - 1.0, 0.0)
    return float(crowding_coefficient) * excess_ratio


def execution_adjusted_edge(
    gross_edge: float,
    spread_cost_value: float = 0.0,
    explicit_fee_cost_value: float = 0.0,
    slippage_cost_value: float = 0.0,
    market_impact_value: float = 0.0,
    adverse_selection_value: float = 0.0,
    implementation_shortfall_value: float = 0.0,
    latency_decay_value: float = 0.0,
    queue_nonfill_penalty_value: float = 0.0,
    partial_fill_penalty_value: float = 0.0,
    capacity_crowding_penalty_value: float = 0.0,
    overfit_fdr_penalty_value: float = 0.0,
) -> float:
    costs = (
        float(spread_cost_value)
        + float(explicit_fee_cost_value)
        + float(slippage_cost_value)
        + float(market_impact_value)
        + float(adverse_selection_value)
        + float(implementation_shortfall_value)
        + float(latency_decay_value)
        + float(queue_nonfill_penalty_value)
        + float(partial_fill_penalty_value)
        + float(capacity_crowding_penalty_value)
        + float(overfit_fdr_penalty_value)
    )
    return float(gross_edge) - costs
