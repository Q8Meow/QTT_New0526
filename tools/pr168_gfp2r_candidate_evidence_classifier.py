#!/usr/bin/env python3
"""Candidate-only evidence classification rules."""

from __future__ import annotations

from typing import Any


def classify_execution(template_id: str, computed_values: dict[str, Any], *, independent_probability_missing: bool) -> str:
    if template_id == "candidate_expected_value_if_independent_probability_exists" and independent_probability_missing:
        return "PROBABILITY_MODEL_REQUIRED_FOR_EDGE"
    if template_id in {"break_even_probability_after_costs", "required_probability_edge"}:
        return "BREAK_EVEN_THRESHOLD_COMPUTED_NON_PROOF"
    if template_id in {
        "spread_depth_execution_cost",
        "fee_tick_min_size_threshold",
        "latency_decay_proxy",
        "capacity_depth_penalty",
    }:
        return "EXECUTION_COST_THRESHOLD_COMPUTED_NON_PROOF"
    if template_id == "no_trade_threshold":
        return "CANDIDATE_NO_TRADE_PREFERRED_NON_PROOF"
    if independent_probability_missing and template_id in {
        "market_implied_probability_baseline",
        "scenario_ladder_stress_candidate",
    }:
        return "BREAK_EVEN_THRESHOLD_COMPUTED_NON_PROOF"
    if computed_values:
        return "PROVISIONAL_DATA_CONSUMER_COMPUTE_NON_PROOF"
    return "REPAIR_REQUIRED_MISSING_FORMULA_INPUT"
