#!/usr/bin/env python3
"""Formula alias and input normalization for PR168-GFP2R."""

from __future__ import annotations

from typing import Any


ALIASES = {
    "mid": "market_implied_probability",
    "midpoint": "market_implied_probability",
    "mid_yes": "market_implied_probability_yes_mid",
    "implied_prob": "market_implied_probability",
    "market_prob": "market_implied_probability",
    "best_yes_ask": "entry_price_yes",
    "best_no_ask": "entry_price_no",
    "yes_bid": "bid_yes",
    "no_bid": "bid_no",
    "candle_close": "price_history_close",
    "trade_price": "recent_trade_price",
}

UNITS = {
    "entry_price": "dollars_per_contract",
    "candidate_cost_stack": "dollars_per_contract",
    "payout_value": "dollars_per_contract",
    "market_implied_probability": "probability",
    "break_even_probability_after_costs": "probability",
    "spread": "dollars_per_contract",
    "depth": "contracts",
    "orderbook_levels": "price_size_levels",
    "price_history": "dollars_per_contract_series",
    "freshness_seconds": "seconds",
    "volatility_proxy": "dollars_per_contract",
    "order_size_bucket": "contracts",
    "top_level_depth": "contracts",
    "explicit_fee": "dollars_per_contract",
    "tick_size": "dollars_per_contract",
    "min_order_size": "contracts",
    "resolution_timestamp": "timestamp",
    "snapshot_timestamp": "timestamp",
    "independent_probability_state": "state",
    "p_resolve_yes_candidate": "probability",
    "candidate_quality_i": "unitless_score",
    "cost_penalty_i": "unitless_score",
    "constraint_refs": "constraint_reference_set",
}


def normalize_input_name(name: str) -> str:
    return ALIASES.get(str(name), str(name))


def normalize_required_inputs(inputs: list[str]) -> list[str]:
    return [normalize_input_name(name) for name in inputs]


def build_alias_rows(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, variant in enumerate(variants, start=1):
        required = variant.get("required_formula_inputs", [])
        rows.append(
            {
                "row_id": f"alias_normalization_{index:05d}",
                "formula_variant_id": variant.get("formula_variant_id"),
                "template_id": variant.get("template_id"),
                "input_alias_normalization_refs": [
                    f"{name}->{normalize_input_name(name)}" for name in required
                ],
                "input_unit_normalization_refs": [
                    f"{normalize_input_name(name)}:{UNITS.get(normalize_input_name(name), 'unknown')}"
                    for name in required
                ],
                "normalized_required_inputs": normalize_required_inputs(list(required)),
            }
        )
    return rows
