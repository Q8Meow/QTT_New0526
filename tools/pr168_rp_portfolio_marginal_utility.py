#!/usr/bin/env python3
"""Portfolio marginal utility and risk features for PR168-RP."""

from __future__ import annotations

from typing import Any


def compute_portfolio_utility(row: dict[str, Any]) -> dict[str, Any]:
    utility = float(row["marginal_utility_score"])
    cvar = max(0.0, float(row.get("adverse_selection_ratio", 0.0)) + float(row.get("cost_drag_ratio", 0.0)) * 0.01)
    common_driver = float(row.get("correlation_cluster_penalty", 0.0))
    concentration = float(row.get("near_duplicate_cluster_size", 1.0)) - 1.0
    capacity_usage = 1.0 - float(row.get("capacity_score", 0.0))
    liquidity_usage = float(row.get("liquidity_drag_ratio", 0.0))
    return {
        "portfolio_marginal_utility": utility,
        "risk_budget_pass_fail": utility > 0,
        "expected_shortfall_cvar": round(cvar, 10),
        "cluster_correlation_penalty": common_driver,
        "common_driver_exposure": common_driver,
        "event_category_exposure": row.get("prediction_market_event_type"),
        "drawdown_contribution": round(cvar + concentration * 0.01, 10),
        "capacity_usage": round(capacity_usage, 10),
        "liquidity_usage": round(liquidity_usage, 10),
        "capital_usage": "NO_CASH_AUTHORITY_POSITION_SIZE_PROXY_ONLY",
        "concentration_penalty": round(max(concentration, 0.0) * 0.01, 10),
        "same_event_stack_penalty": 0.0 if concentration <= 0 else round(concentration * 0.01, 10),
        "same_resolution_cluster_penalty": round(common_driver, 10),
        "portfolio_repair_candidate_route": "PR168_RP_PortfolioRepairCandidateQueue.report.json",
    }
