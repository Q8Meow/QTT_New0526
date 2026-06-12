"""Deterministic materialized formula and algorithm snippets for PR166-SF."""

from __future__ import annotations

from typing import Mapping


def repaired_net_edge_after_costs(values: Mapping[str, float]) -> float:
    return round(
        float(values.get("gross_edge", 0.0))
        - float(values.get("fee_cost_component", 0.0))
        - float(values.get("spread_cost_component", 0.0))
        - float(values.get("slippage_cost_component", 0.0))
        - float(values.get("market_impact_cost_component", 0.0))
        - float(values.get("latency_cost_component", 0.0))
        - float(values.get("liquidity_cost_component", 0.0))
        - float(values.get("settlement_cost_component", 0.0)),
        6,
    )


def brier_proxy(model_probability: float, market_probability: float) -> float:
    return round((float(model_probability) - float(market_probability)) ** 2, 6)


def qubo_binary_selection_objective(linear: Mapping[str, float]) -> dict[str, object]:
    return {
        "objective_direction": "MAXIMIZE_REPAIRED_RETEST_READINESS_MINUS_COST_DRAG",
        "variables": sorted(linear),
        "linear_coefficients": {key: round(float(value), 6) for key, value in linear.items()},
        "quadratic_coefficients": {},
        "classical_comparator": "GREEDY_REPAIR_PRIORITY_AND_DIVERSIFICATION_BASELINE",
    }
