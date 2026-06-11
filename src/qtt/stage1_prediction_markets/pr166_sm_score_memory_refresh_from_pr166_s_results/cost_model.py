"""Execution-adjusted economic computations."""

from __future__ import annotations

from typing import Any

from .normalization import clamp, round6


COST_FIELDS = (
    "spread_cost",
    "maker_taker_fees",
    "slippage_cost",
    "market_impact_cost",
    "latency_drag",
    "liquidity_drag",
    "adverse_selection_drag",
    "settlement_payoff_adjustment",
)


def numeric(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def net_edge_after_costs(cost_row: dict[str, Any]) -> float:
    gross = numeric(cost_row, "gross_edge")
    return round6(gross - sum(numeric(cost_row, field) for field in COST_FIELDS))


def cost_metrics(cost_row: dict[str, Any]) -> dict[str, float]:
    gross = numeric(cost_row, "gross_edge")
    abs_gross = max(abs(gross), 0.000001)
    total_cost = sum(numeric(cost_row, field) for field in COST_FIELDS)
    latency_drag = numeric(cost_row, "latency_drag")
    liquidity_drag = numeric(cost_row, "liquidity_drag")
    adverse_selection = numeric(cost_row, "adverse_selection_drag")
    settlement = numeric(cost_row, "settlement_payoff_adjustment")
    return {
        "gross_edge": round6(gross),
        "spread_cost": round6(numeric(cost_row, "spread_cost")),
        "maker_taker_fees": round6(numeric(cost_row, "maker_taker_fees")),
        "slippage_cost": round6(numeric(cost_row, "slippage_cost")),
        "market_impact_cost": round6(numeric(cost_row, "market_impact_cost")),
        "latency_drag": round6(latency_drag),
        "liquidity_drag": round6(liquidity_drag),
        "adverse_selection_drag": round6(adverse_selection),
        "settlement_payoff_adjustment": round6(settlement),
        "implementation_shortfall_proxy": round6(total_cost),
        "net_edge_after_costs": net_edge_after_costs(cost_row),
        "cost_drag_ratio": round6(total_cost / abs_gross),
        "latency_drag_ratio": round6(latency_drag / abs_gross),
        "liquidity_drag_ratio": round6(liquidity_drag / abs_gross),
        "adverse_selection_ratio": round6(adverse_selection / abs_gross),
        "settlement_sensitivity_ratio": round6(settlement / abs_gross),
    }


def fill_quality_from_confidence(confidence_row: dict[str, Any]) -> float:
    return round6(clamp(numeric(confidence_row, "fill_quality_score", 0.5)))
