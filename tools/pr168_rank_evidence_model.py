#!/usr/bin/env python3
"""Shared evidence row helpers for PR168-RANK."""

from __future__ import annotations

import math
import re
from typing import Any


NUMERIC_SCORE_COMPONENTS = [
    "fill_adjusted_expected_pnl",
    "net_expected_pnl_candidate",
    "execution_adjusted_edge",
    "lower_confidence_bound_edge",
    "no_trade_comparison_margin",
    "total_tca_cost",
    "fill_probability",
    "latency_budget_usage",
    "capacity_crowding_penalty",
    "overfit_fdr_penalty",
    "portfolio_marginal_utility",
    "expected_shortfall_cvar_candidate",
    "scenario_ladder_score",
    "calibration_quality_score",
    "regime_stability_score",
    "quantum_structural_readiness_score",
    "critical_gap_penalty",
    "agent_route_completeness_score",
    "no_orphan_score",
    "compute_budget_penalty",
    "order_policy_quality_score",
    "candidate_stack_role_completeness_score",
    "edge_capture_attribution_score",
    "negative_recovery_potential_score",
    "maker_taker_tradeoff_score",
    "threshold_surface_quality_score",
    "size_price_time_sensitivity_score",
    "scenario_stress_survival_score",
    "terminal_lifecycle_route_score",
]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def number(value: Any, default: float = 0.0) -> float:
    if is_number(value):
        return float(value)
    return default


def result_ref_from_candidate_id(candidate_id: str | None) -> str:
    text = str(candidate_id or "")
    match = re.search(r"PR168_RP_RESULT::\d+", text)
    return match.group(0) if match else text


def total_tca_from_pretrade(row: dict[str, Any]) -> float:
    return round(
        sum(
            number(row.get(field))
            for field in (
                "explicit_fee_cost",
                "spread_cost",
                "slippage_cost",
                "adverse_selection_penalty",
                "implementation_shortfall",
                "latency_decay",
                "market_impact",
                "queue_nonfill_penalty",
                "partial_fill_penalty",
                "stale_orderbook_penalty",
            )
        ),
        10,
    )


def score_components_from_pretrade(row: dict[str, Any]) -> dict[str, float]:
    total_tca = total_tca_from_pretrade(row)
    fill_adjusted = number(row.get("fill_adjusted_expected_pnl"))
    lcb = number(row.get("lower_confidence_bound_edge"))
    no_trade_margin = number(row.get("no_trade_comparison_margin"))
    capacity = number(row.get("capacity_crowding_penalty"))
    overfit = number(row.get("overfit_fdr_penalty"))
    latency_ms = number(row.get("expected_latency"))
    candidate_score = number(row.get("candidate_score_money"))
    return {
        "fill_adjusted_expected_pnl": round(fill_adjusted, 10),
        "net_expected_pnl_candidate": round(number(row.get("expected_net_pnl"), candidate_score), 10),
        "execution_adjusted_edge": round(number(row.get("execution_adjusted_edge"), fill_adjusted), 10),
        "lower_confidence_bound_edge": round(lcb, 10),
        "no_trade_comparison_margin": round(no_trade_margin, 10),
        "total_tca_cost": total_tca,
        "fill_probability": round(number(row.get("expected_fill")), 10),
        "latency_budget_usage": round(latency_ms / max(number(row.get("latency_budget_ms"), 1.0), 1.0), 10),
        "capacity_crowding_penalty": round(capacity, 10),
        "overfit_fdr_penalty": round(overfit, 10),
        "portfolio_marginal_utility": round(number(row.get("portfolio_marginal_utility")), 10),
        "expected_shortfall_cvar_candidate": round(number(row.get("expected_shortfall_cvar")), 10),
        "scenario_ladder_score": 0.0 if lcb <= 0 else 1.0,
        "calibration_quality_score": 0.5,
        "regime_stability_score": 0.5,
        "quantum_structural_readiness_score": 0.0,
        "critical_gap_penalty": 1.0 if row.get("champion_eligibility_blockers") else 0.0,
        "agent_route_completeness_score": 1.0 if row.get("owning_agent") else 0.0,
        "no_orphan_score": 1.0 if row.get("no_orphan_status") else 0.0,
        "compute_budget_penalty": 0.0,
        "order_policy_quality_score": 1.0 if row.get("order_type_candidate") == "NO_TRADE_CANDIDATE" else 0.25,
        "candidate_stack_role_completeness_score": 1.0,
        "edge_capture_attribution_score": 1.0 if fill_adjusted > 0 else 0.0,
        "negative_recovery_potential_score": 0.25 if fill_adjusted < 0 else 0.0,
        "maker_taker_tradeoff_score": 0.5,
        "threshold_surface_quality_score": 1.0,
        "size_price_time_sensitivity_score": 1.0,
        "scenario_stress_survival_score": 0.0 if lcb <= 0 else 1.0,
        "terminal_lifecycle_route_score": 1.0 if row.get("champion_eligible") is False else 0.0,
    }


def rank_score(components: dict[str, float]) -> float:
    positive = (
        components["fill_adjusted_expected_pnl"]
        + components["lower_confidence_bound_edge"]
        + components["execution_adjusted_edge"]
        + components["no_trade_comparison_margin"]
        + components["portfolio_marginal_utility"]
        + components["order_policy_quality_score"]
        + components["candidate_stack_role_completeness_score"]
    )
    negative = (
        components["total_tca_cost"]
        + components["overfit_fdr_penalty"]
        + components["capacity_crowding_penalty"]
        + components["latency_budget_usage"]
        + abs(components["expected_shortfall_cvar_candidate"])
        + components["critical_gap_penalty"]
    )
    return round(positive - negative, 10)
