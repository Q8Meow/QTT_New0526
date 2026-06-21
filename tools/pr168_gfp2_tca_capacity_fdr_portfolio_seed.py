#!/usr/bin/env python3
"""TCA, capacity, FDR, calibration, and portfolio seed rows for PR168-GFP2."""

from __future__ import annotations

from typing import Any


TCA_COMPONENTS = (
    "arrival_mid_or_decision_price",
    "entry_limit_price",
    "expected_fill_price",
    "simulated_replay_fill_price",
    "spread_cross_or_capture_cost",
    "explicit_fee_cost",
    "expected_slippage_cost",
    "adverse_selection_cost",
    "market_impact_depth_cost",
    "queue_position_cost",
    "missed_fill_cost",
    "cancel_replace_cost",
    "latency_decay_cost",
    "opportunity_cost",
    "settlement_cash_carry_cost",
    "implementation_shortfall_total",
    "implementation_shortfall_per_contract",
    "implementation_shortfall_bps_or_cents",
)


def seed_rows(seed_family: str, components: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {
            "seed_family": seed_family,
            "field_name": component,
            "required_input_state": "GAP_ROUTED_PENDING_ACCEPTED_REAL_DATA",
            "candidate_only_flag": True,
            "accepted_truth_flag": False,
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Risk/Capacity/TCA Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for component in components
    ]


def tca_rows() -> list[dict[str, Any]]:
    return seed_rows("tca_decomposition", TCA_COMPONENTS)


def capacity_rows() -> list[dict[str, Any]]:
    return seed_rows(
        "capacity_crowding",
        (
            "book_depth_at_price",
            "book_depth_within_edge_band",
            "order_size",
            "participation_rate",
            "market_daily_volume_bucket",
            "event_open_interest_or_liquidity_proxy",
            "spread_bucket",
            "liquidity_decay_estimate",
            "crowding_cluster_id",
            "same_event_family_exposure",
            "capacity_pass_flag",
            "capacity_penalty",
        ),
    )


def calibration_rows() -> list[dict[str, Any]]:
    return seed_rows(
        "probability_calibration",
        ("probability_model_id", "calibration_window_ref", "sample_size", "base_rate", "reliability_bin_id", "brier_score_seed", "log_loss_seed", "ece_seed", "calibration_gap_reason", "calibration_lcb_allowed_flag"),
    )


def overfit_fdr_rows() -> list[dict[str, Any]]:
    return seed_rows(
        "overfit_fdr",
        ("trial_family_id", "trial_count", "variant_count", "parameter_sweep_count", "family_p_value_or_metric_ref", "fdr_method", "deflated_metric_ref", "purged_walk_forward_ref", "cpcv_split_ref", "embargo_window_ref", "overfit_penalty", "promotion_block_if_uncontrolled_flag"),
    )


def portfolio_rows() -> list[dict[str, Any]]:
    return seed_rows(
        "portfolio_marginal_utility",
        ("delta_expected_portfolio_pnl", "lambda_risk", "delta_portfolio_risk", "crowding_penalty", "correlation_cluster_penalty", "capacity_penalty", "drawdown_tail_penalty"),
    )
