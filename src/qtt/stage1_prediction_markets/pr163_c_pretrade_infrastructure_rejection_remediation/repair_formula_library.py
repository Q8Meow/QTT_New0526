"""Executable deterministic repair formulas for PR163-C."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _round(value: float, places: int = 6) -> float:
    return round(float(value), places)


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(float(value), float(lower)), float(upper))


def fee_component(notional: float, fixed_fee: float, percentage_fee: float, fee_cap: float) -> float:
    return _round(min(float(fee_cap), float(fixed_fee) + float(notional) * float(percentage_fee)))


def expected_slippage_bps(spread_bps: float, impact_proxy: float, adverse_selection_penalty: float) -> float:
    return _round(float(spread_bps) / 2.0 + float(impact_proxy) + float(adverse_selection_penalty), 4)


def latency_stale_data_cost(expected_price_move_per_ms: float, latency_ms: float, stale_data_penalty: float) -> float:
    return _round(float(expected_price_move_per_ms) * float(latency_ms) + float(stale_data_penalty), 4)


def fill_probability(order_size_to_depth_ratio: float, adverse_selection_penalty: float) -> float:
    value = 1.0 - 0.6 * float(order_size_to_depth_ratio) - float(adverse_selection_penalty)
    return _round(clamp(value, 0.05, 0.99), 4)


def expected_net_profit_candidate(
    gross_edge_candidate: float,
    exchange_fee_component: float,
    spread_cross_component: float,
    slippage_component: float,
    latency_adverse_selection_component: float,
    queue_nonfill_opportunity_cost_component: float,
    cancel_replace_component: float,
    capital_lock_component: float,
    settlement_delay_component: float,
    stale_data_penalty_component: float,
    operational_error_component: float,
) -> float:
    costs = (
        exchange_fee_component
        + spread_cross_component
        + slippage_component
        + latency_adverse_selection_component
        + queue_nonfill_opportunity_cost_component
        + cancel_replace_component
        + capital_lock_component
        + settlement_delay_component
        + stale_data_penalty_component
        + operational_error_component
    )
    return _round(float(gross_edge_candidate) - costs, 6)


def implementation_shortfall(arrival_price_candidate: float, simulated_execution_price: float, side_multiplier: float) -> float:
    return _round((float(simulated_execution_price) - float(arrival_price_candidate)) * float(side_multiplier), 6)


def tick_size_quantize(price: float, tick_size: float) -> float:
    tick = float(tick_size)
    if tick <= 0:
        raise ValueError("tick_size must be positive")
    return _round(round(float(price) / tick) * tick, 6)


def venue_price_normalize(raw_price: float, price_scale: float) -> float:
    return _round(clamp(float(raw_price) * float(price_scale), 0.0, 1.0), 6)


FORMULAS: dict[str, Callable[..., float]] = {
    "PR163C_FORMULA::FEE_COMPONENT": fee_component,
    "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS": expected_slippage_bps,
    "PR163C_FORMULA::LATENCY_STALE_DATA_COST": latency_stale_data_cost,
    "PR163C_FORMULA::FILL_PROBABILITY": fill_probability,
    "PR163C_FORMULA::EXPECTED_NET_PROFIT_CANDIDATE": expected_net_profit_candidate,
    "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL": implementation_shortfall,
    "PR163C_FORMULA::TICK_SIZE_QUANTIZE": tick_size_quantize,
    "PR163C_FORMULA::VENUE_PRICE_NORMALIZE": venue_price_normalize,
}


FORMULA_METADATA: dict[str, dict[str, Any]] = {
    "PR163C_FORMULA::FEE_COMPONENT": {
        "formula_expression": "min(fee_cap, fixed_fee + notional * percentage_fee)",
        "input_fields": ["notional", "fixed_fee", "percentage_fee", "fee_cap"],
        "output_fields": ["exchange_fee_component"],
    },
    "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS": {
        "formula_expression": "spread_bps / 2 + impact_proxy + adverse_selection_penalty",
        "input_fields": ["spread_bps", "impact_proxy", "adverse_selection_penalty"],
        "output_fields": ["expected_slippage_bps"],
    },
    "PR163C_FORMULA::LATENCY_STALE_DATA_COST": {
        "formula_expression": "expected_price_move_per_ms * latency_ms + stale_data_penalty",
        "input_fields": ["expected_price_move_per_ms", "latency_ms", "stale_data_penalty"],
        "output_fields": ["latency_adverse_selection_component"],
    },
    "PR163C_FORMULA::FILL_PROBABILITY": {
        "formula_expression": "clamp(1 - 0.6 * order_size_to_depth_ratio - adverse_selection_penalty, 0.05, 0.99)",
        "input_fields": ["order_size_to_depth_ratio", "adverse_selection_penalty"],
        "output_fields": ["fill_probability_candidate"],
    },
    "PR163C_FORMULA::EXPECTED_NET_PROFIT_CANDIDATE": {
        "formula_expression": "gross_edge_candidate - exchange_fee_component - spread_cross_component - slippage_component - latency_adverse_selection_component - queue_nonfill_opportunity_cost_component - cancel_replace_component - capital_lock_component - settlement_delay_component - stale_data_penalty_component - operational_error_component",
        "input_fields": [
            "gross_edge_candidate",
            "exchange_fee_component",
            "spread_cross_component",
            "slippage_component",
            "latency_adverse_selection_component",
            "queue_nonfill_opportunity_cost_component",
            "cancel_replace_component",
            "capital_lock_component",
            "settlement_delay_component",
            "stale_data_penalty_component",
            "operational_error_component",
        ],
        "output_fields": ["expected_net_profit_candidate"],
    },
    "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL": {
        "formula_expression": "(simulated_execution_price - arrival_price_candidate) * side_multiplier",
        "input_fields": ["arrival_price_candidate", "simulated_execution_price", "side_multiplier"],
        "output_fields": ["implementation_shortfall_candidate"],
    },
    "PR163C_FORMULA::TICK_SIZE_QUANTIZE": {
        "formula_expression": "round(price / tick_size) * tick_size",
        "input_fields": ["price", "tick_size"],
        "output_fields": ["limit_price_candidate"],
    },
    "PR163C_FORMULA::VENUE_PRICE_NORMALIZE": {
        "formula_expression": "clamp(raw_price * price_scale, 0, 1)",
        "input_fields": ["raw_price", "price_scale"],
        "output_fields": ["normalized_price_candidate"],
    },
}


def apply_formula(formula_ref: str, inputs: dict[str, float]) -> float:
    return FORMULAS[formula_ref](**inputs)


def registry_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for formula_ref in sorted(FORMULA_METADATA):
        meta = FORMULA_METADATA[formula_ref]
        rows.append(
            {
                "formula_ref": formula_ref,
                "formula_id": formula_ref,
                "formula_expression": meta["formula_expression"],
                "executable_function": FORMULAS[formula_ref].__name__,
                "input_fields": meta["input_fields"],
                "output_fields": meta["output_fields"],
                "formula_authority_status": "REPLAY_PAPER_CANDIDATE_FORMULA_NOT_SOURCE_TRUTH",
                "validation_status": "PASS",
            }
        )
    return rows
