#!/usr/bin/env python3
"""Pre-trade simulation kernel for non-live PR168-RP candidates."""

from __future__ import annotations

from typing import Any


POLICY_MULTIPLIERS = {
    "PASSIVE_MAKER_LIMIT": {"fill": 0.85, "spread": 0.50, "slippage": 0.40, "latency": 1.20, "impact": 0.70},
    "MIDPOINT_IMPROVING_LIMIT": {"fill": 0.90, "spread": 0.75, "slippage": 0.60, "latency": 1.00, "impact": 0.80},
    "AGGRESSIVE_MARKETABLE_LIMIT": {"fill": 1.00, "spread": 1.10, "slippage": 1.20, "latency": 0.80, "impact": 1.00},
    "FAK_STYLE_IMMEDIATE_CANDIDATE": {"fill": 0.75, "spread": 1.15, "slippage": 1.10, "latency": 0.70, "impact": 0.90},
    "SPLIT_ORDER_CHILD_SLICE": {"fill": 0.95, "spread": 0.80, "slippage": 0.55, "latency": 1.25, "impact": 0.50},
    "WAIT_FOR_BETTER_SPREAD": {"fill": 0.65, "spread": 0.45, "slippage": 0.30, "latency": 1.60, "impact": 0.60},
    "NO_TRADE_CANDIDATE": {"fill": 0.0, "spread": 0.0, "slippage": 0.0, "latency": 0.0, "impact": 0.0},
}


def simulate_pretrade_candidate(candidate: dict[str, Any], computed: dict[str, Any]) -> dict[str, Any]:
    policy = str(candidate["order_type_candidate"])
    metrics = computed["metrics"]
    mult = POLICY_MULTIPLIERS[policy]
    if policy == "NO_TRADE_CANDIDATE":
        score = 0.0
        fill_probability = 0.0
        no_trade_margin = 0.0
    else:
        fill_probability = min(1.0, float(metrics["fill_probability"]) * float(mult["fill"]))
        spread_cost = float(metrics["spread_cost"]) * float(mult["spread"])
        slippage = float(metrics["slippage_cost"]) * float(mult["slippage"])
        market_impact = float(metrics["market_impact"]) * float(mult["impact"])
        latency_decay = float(metrics["latency_decay"]) * float(mult["latency"])
        base_edge = (
            float(metrics["predicted_probability"])
            - float(metrics["market_implied_probability"])
            - float(metrics["explicit_fee_cost"])
            - spread_cost
            - slippage
            - market_impact
            - float(metrics["adverse_selection_penalty"])
            - float(metrics["implementation_shortfall"])
            - latency_decay
            - float(metrics["queue_nonfill_penalty"])
            - float(metrics["partial_fill_penalty"])
            - float(metrics["stale_orderbook_penalty"])
            - float(metrics["capacity_crowding_penalty"])
            - float(metrics["overfit_fdr_penalty"])
        )
        score = (
            fill_probability * float(metrics["position_size"]) * base_edge
            - float(metrics["no_fill_opportunity_cost"])
            - float(metrics["partial_fill_residual_risk"])
            - float(metrics["expected_shortfall_cvar"])
            + float(metrics["portfolio_marginal_utility"])
        )
        no_trade_margin = score
    expected_latency = int(float(computed["microstructure"]["book_staleness"]))
    latency_budget_ms = int(float(computed["source_rows"]["microstructure"]["latency_budget_ms"]))
    latency_pass = expected_latency <= latency_budget_ms
    final_status = "PRETRADE_NO_TRADE_DOMINATES" if no_trade_margin <= 0 else "PRETRADE_SIMULATION_INPUT_GAP"
    return {
        **candidate,
        "expected_fill": round(fill_probability * float(candidate["quantity_candidate"]), 10),
        "expected_price": candidate["limit_price_candidate"],
        "expected_latency": expected_latency,
        "expected_adverse_selection": metrics["adverse_selection_penalty"],
        "expected_unfilled_quantity": round(float(candidate["quantity_candidate"]) * (1.0 - fill_probability), 10),
        "expected_net_pnl": round(score, 10),
        "fill_adjusted_expected_pnl": round(score, 10),
        "lower_confidence_bound_edge": metrics["lower_confidence_bound_edge"],
        "explicit_fee_cost": metrics["explicit_fee_cost"],
        "spread_cost": round(float(metrics["spread_cost"]) * float(mult["spread"]), 10),
        "slippage_cost": round(float(metrics["slippage_cost"]) * float(mult["slippage"]), 10),
        "market_impact": round(float(metrics["market_impact"]) * float(mult["impact"]), 10),
        "adverse_selection_penalty": metrics["adverse_selection_penalty"],
        "implementation_shortfall": metrics["implementation_shortfall"],
        "latency_decay": round(float(metrics["latency_decay"]) * float(mult["latency"]), 10),
        "queue_nonfill_penalty": metrics["queue_nonfill_penalty"],
        "partial_fill_penalty": metrics["partial_fill_penalty"],
        "stale_orderbook_penalty": metrics["stale_orderbook_penalty"],
        "capacity_crowding_penalty": metrics["capacity_crowding_penalty"],
        "overfit_fdr_penalty": metrics["overfit_fdr_penalty"],
        "portfolio_marginal_utility": metrics["portfolio_marginal_utility"],
        "expected_shortfall_cvar": metrics["expected_shortfall_cvar"],
        "worst_case_loss": round(abs(score) + float(metrics["expected_shortfall_cvar"]), 10),
        "latency_budget_ms": latency_budget_ms,
        "latency_budget_pass_fail": latency_pass,
        "no_trade_comparison_margin": round(no_trade_margin, 10),
        "final_decision_status": final_status,
        "candidate_score_money": round(score, 10),
    }
