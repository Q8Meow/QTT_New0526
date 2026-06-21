#!/usr/bin/env python3
"""Alpha-capture and order simulation seed rows for PR168-GFP2."""

from __future__ import annotations

from typing import Any


ALPHA_FAMILIES = (
    "execution_adjusted_ranking_seed",
    "implementation_shortfall_tca_seed",
    "fill_probability_seed",
    "queue_position_missed_fill_seed",
    "latency_decay_seed",
    "capacity_crowding_seed",
    "overfit_fdr_trial_family_seed",
    "deflated_metric_seed",
    "purged_walk_forward_or_cpcv_seed",
    "probability_calibration_seed",
    "brier_logloss_ece_seed",
    "portfolio_diversification_seed",
    "correlation_event_family_cluster_seed",
    "marginal_utility_seed",
    "regime_conditioned_memory_seed",
    "no_trade_baseline_seed",
    "champion_challenger_no_trade_seed",
    "scenario_ladder_seed",
    "negative_memory_candidate_seed",
    "trade_order_simulation_stack_seed",
    "candidate_stack_search_space_seed",
    "execution_policy_alternative_seed",
)


def alpha_capture_rows() -> list[dict[str, Any]]:
    return [
        {
            "seed_family": family,
            "formula_ref": "PR168_GFP2_ExecutionAdjustedExpectedValueFormulaRegistry.report.json",
            "required_data_state": "GAP_ROUTE_MISSING_ACCEPTED_REAL_MARKET_DATA",
            "candidate_only_flag": True,
            "creates_champion_or_live_authority_flag": False,
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Alpha Recovery Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for family in ALPHA_FAMILIES
    ]


def execution_adjusted_formula_rows() -> list[dict[str, Any]]:
    formulas = {
        "expected_gross_pnl_yes": "p_resolve_yes_calibrated * payout_value - entry_price",
        "expected_gross_pnl_no": "(1 - p_resolve_yes_calibrated) * payout_value - entry_price",
        "expected_cost_stack": "explicit_fees + expected_half_spread_or_crossing_cost + expected_slippage + expected_adverse_selection_cost + expected_latency_decay_penalty + expected_market_impact_or_depth_penalty + expected_opportunity_or_cash_carry_cost + expected_settlement_friction_cost",
        "expected_pnl_after_costs": "expected_gross_pnl - expected_cost_stack",
        "fill_adjusted_expected_pnl": "fill_probability * expected_pnl_after_costs - (1 - fill_probability) * missed_alpha_or_cancel_cost",
        "execution_adjusted_edge": "calibrated_probability_edge - spread_cost - explicit_fees - expected_slippage - adverse_selection_cost - latency_decay_penalty - capacity_depth_penalty",
        "lower_confidence_bound_edge": "mean_edge - z_alpha * standard_error_edge only when sufficient provenance exists",
        "no_trade_margin": "candidate_lcb_after_costs - no_trade_baseline_lcb",
        "portfolio_marginal_utility": "delta_expected_portfolio_pnl - lambda_risk * delta_portfolio_risk - crowding_penalty - correlation_cluster_penalty - capacity_penalty - drawdown_tail_penalty",
    }
    return [
        {
            "formula_name": name,
            "formula_expression": expression,
            "accepted_truth_flag": False,
            "candidate_seed_only_flag": True,
            "gap_route_if_inputs_missing": "PR168-RP2",
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Replay Paper Recompute Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for name, expression in formulas.items()
    ]


def candidate_stack_search_space_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for side in ("YES", "NO", "BOTH_HYPOTHESIS"):
        for order_policy in ("maker_limit", "taker_cross", "passive_join", "pegged", "wait", "cancel_replace_candidate", "no_trade"):
            rows.append(
                {
                    "candidate_stack_seed_id": f"PR168_GFP2_STACK::{side}::{order_policy}",
                    "side": side,
                    "order_policy": order_policy,
                    "venue": "VENUE_PENDING_BINDING",
                    "accepted_real_data_eligibility": "PENDING_PR168_RP2",
                    "candidate_only_flag": True,
                    "source_provenance_tier": "GAP_ROUTED",
                    "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                    "agent_owner": "Ranking Agent",
                    "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
                }
            )
    return rows


def order_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "order_policy": policy,
            "policy_seed_only_flag": True,
            "live_order_authority_created_flag": False,
            "accepted_market_data_required_flag": True,
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Execution/TCA Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for policy in ("maker_limit", "taker_cross", "passive_join", "pegged", "wait", "cancel_replace_candidate", "no_trade")
    ]
