#!/usr/bin/env python3
"""FDR, calibration, portfolio, regime, and scenario seed builders."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_fdr_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"fdr_trial_family_seed_{index:05d}",
            "candidate_stack_id": stack["candidate_stack_id"],
            "trial_family_id": stack["overfit_fdr_trial_family_id"],
            "parameter_family_id": f"parameter_family::{stack.get('side')}::{stack.get('order_policy')}",
            "formula_variant_family_id": f"formula_variant_family::{stack.get('formula_variant_id')}",
            "fdr_control_required_flag": True,
            "deflated_sharpe_ready_flag": False,
            "purged_validation_ready_flag": False,
            "repair_route": "RANK2_FDR_AND_PURGED_VALIDATION_REQUIRED",
            **route_defaults("risk", data1_refs=data1_report_refs(), data1a_refs=data1a_report_refs(), upstream_refs=[stack["candidate_stack_id"]]),
        }
        for index, stack in enumerate(stack_rows, start=1)
    ]


def build_calibration_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"calibration_sample_size_gap_{index:05d}",
            "candidate_stack_id": stack["candidate_stack_id"],
            "sample_size_sufficient_flag": False,
            "candidate_lcb_edge_ready_flag": False,
            "calibration_gap_code": "INDEPENDENT_PROBABILITY_MODEL_AND_SAMPLE_SIZE_REQUIRED",
            "repair_route": "BIND_INDEPENDENT_PROBABILITY_MODEL_THEN_RP2_CALIBRATION",
            **route_defaults("risk", data1_refs=data1_report_refs(), data1a_refs=data1a_report_refs(), upstream_refs=[stack["candidate_stack_id"]]),
        }
        for index, stack in enumerate(stack_rows, start=1)
    ]


def build_portfolio_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"portfolio_marginal_utility_seed_{index:05d}",
            "candidate_stack_id": stack["candidate_stack_id"],
            "event_family": f"{stack.get('venue')}::{stack.get('market_id_or_token_id')}",
            "venue": stack.get("venue"),
            "category": "prediction_market_public_candidate",
            "token_or_outcome_relationship": stack.get("side"),
            "correlation_cluster_candidate": stack["portfolio_marginal_utility_cluster_id"],
            "concentration_risk_seed": "SAME_MARKET_AND_EVENT_FAMILY_PENALTY_REQUIRED",
            "marginal_utility_ready_flag": False,
            **route_defaults("ranking", data1_refs=data1_report_refs(), data1a_refs=data1a_report_refs(), upstream_refs=[stack["candidate_stack_id"]]),
        }
        for index, stack in enumerate(stack_rows, start=1)
    ]


def build_regime_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"regime_conditioned_memory_seed_{index:05d}",
            "candidate_stack_id": stack["candidate_stack_id"],
            "regime_condition_id": stack["regime_condition_id"],
            "liquidity_bucket": stack.get("liquidity_bucket"),
            "spread_bucket": stack.get("spread_bucket"),
            "volatility_bucket": "PRICE_HISTORY_VOLATILITY_SEED_OR_GAP",
            "time_to_resolution_bucket": "MARKET_LIFECYCLE_SEED_OR_GAP",
            "venue": stack.get("venue"),
            "market_lifecycle": "DATA1A_MARKET_LIFECYCLE_CANDIDATE",
            "memory_route": "PR165B_CONDITION_SCOPED_MEMORY_PREP",
            **route_defaults("ranking", data1_refs=data1_report_refs(), data1a_refs=data1a_report_refs(), upstream_refs=[stack["candidate_stack_id"]]),
        }
        for index, stack in enumerate(stack_rows, start=1)
    ]


def build_scenario_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenarios = [
        "thin_book",
        "wide_spread",
        "stale_data",
        "fee_increase",
        "latency_decay",
        "partial_fill",
        "probability_model_missing",
        "historical_full_book_missing",
        "no_trade",
    ]
    return [
        {
            "row_id": f"scenario_ladder_seed_{index:05d}",
            "candidate_stack_id": stack["candidate_stack_id"],
            "scenario_ladder": scenarios,
            "scenario_ladder_seed_ref": stack["scenario_ladder_seed_ref"],
            "no_trade_included_flag": True,
            "historical_full_book_missing_scenario_included_flag": True,
            **route_defaults("risk", data1_refs=data1_report_refs(), data1a_refs=data1a_report_refs(), upstream_refs=[stack["candidate_stack_id"]]),
        }
        for index, stack in enumerate(stack_rows, start=1)
    ]
