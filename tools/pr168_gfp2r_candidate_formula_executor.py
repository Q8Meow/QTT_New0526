#!/usr/bin/env python3
"""Candidate-only and provisional formula execution for PR168-GFP2R."""

from __future__ import annotations

from statistics import pstdev
from typing import Any

from tools.pr168_gfp2r_break_even_thresholds import (
    break_even_probability_after_costs,
    required_probability_edge,
)
from tools.pr168_gfp2r_candidate_evidence_classifier import classify_execution
from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_formula_input_resolver import resolved_inputs_for_variant
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs
from tools.pr168_gfp2r_market_implied_probability import market_implied_probability


def _round(value: float | None) -> float | None:
    return round(float(value), 6) if value is not None else None


def _price_returns(prices: list[float]) -> list[float]:
    returns: list[float] = []
    for left, right in zip(prices, prices[1:]):
        returns.append(float(right) - float(left))
    return returns


def _compute(variant: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    inputs = resolved_inputs_for_variant(variant)
    kind = variant.get("template_id")
    missing = list(variant.get("missing_formula_inputs", []))
    if missing or not variant.get("provisional_compute_eligible_flag"):
        return False, {}, missing
    entry = inputs.get("entry_price")
    payout = inputs.get("payout_value", 1.0)
    cost = inputs.get("candidate_cost_stack")
    market_prob = inputs.get("market_implied_probability")
    values: dict[str, Any] = {}
    if kind == "market_implied_probability_baseline":
        values["market_implied_probability"] = market_implied_probability(entry, payout)
    elif kind == "break_even_probability_after_costs":
        values["break_even_probability_after_costs"] = break_even_probability_after_costs(entry, cost, payout)
    elif kind == "required_probability_edge":
        be = break_even_probability_after_costs(entry, cost, payout)
        values["break_even_probability_after_costs"] = be
        values["required_probability_edge"] = required_probability_edge(be, market_prob)
    elif kind == "spread_depth_execution_cost":
        spread = inputs.get("spread")
        depth = float(inputs.get("depth") or 0.0)
        depth_slippage = 1.0 / max(depth, 1.0)
        values["spread_depth_execution_cost"] = _round(float(spread or 0.0) / 2.0 + depth_slippage)
    elif kind == "fillable_size_at_price_band":
        values["fillable_size_at_price_band"] = _round(float(inputs.get("depth") or 0.0))
    elif kind == "fillable_size_at_edge_band":
        values["fillable_size_at_edge_band"] = _round(max(0.0, float(inputs.get("depth") or 0.0) * 0.5))
    elif kind == "orderbook_imbalance":
        bid = float(inputs.get("bid_depth") or 0.0)
        ask = float(inputs.get("ask_depth") or 0.0)
        values["orderbook_imbalance"] = _round((bid - ask) / max(bid + ask, 1.0))
    elif kind == "book_slope_proxy":
        values["book_slope_proxy"] = _round(float(inputs.get("spread") or 0.0) / max(float(inputs.get("depth") or 0.0), 1.0))
    elif kind == "short_horizon_price_momentum":
        prices = list(inputs.get("price_history") or [])
        values["short_horizon_price_momentum"] = _round(float(prices[-1]) - float(prices[0])) if len(prices) > 1 else None
    elif kind == "price_history_volatility_proxy":
        returns = _price_returns(list(inputs.get("price_history") or []))
        values["price_history_volatility_proxy"] = _round(pstdev(returns)) if len(returns) > 1 else 0.0
    elif kind == "latency_decay_proxy":
        values["latency_decay_proxy"] = _round(
            float(inputs.get("freshness_seconds") or 0.0) * float(inputs.get("volatility_proxy") or 0.0) / 86400.0
        )
    elif kind == "capacity_depth_penalty":
        values["capacity_depth_penalty"] = _round(
            float(inputs.get("order_size_bucket") or 0.0) / max(float(inputs.get("top_level_depth") or 0.0), 1.0)
        )
    elif kind == "fee_tick_min_size_threshold":
        values["fee_tick_min_size_threshold"] = _round(
            float(inputs.get("explicit_fee") or 0.0)
            + float(inputs.get("tick_size") or 0.0) * float(inputs.get("min_order_size") or 0.0)
        )
    elif kind == "time_to_resolution_lifecycle_feature":
        context = variant.get("market_context", {})
        values["time_to_resolution_seconds"] = _round(float(context.get("resolution_seconds", 0.0) or 0.0))
    elif kind == "no_trade_threshold":
        values["no_trade_threshold"] = _round(float(cost or 0.0) + 0.01)
    elif kind == "scenario_ladder_stress_candidate":
        be = break_even_probability_after_costs(entry, cost, payout)
        values["scenario_ladder_stressed_break_even"] = _round(float(be or 0.0) + 2.0 * float(cost or 0.0))
    elif kind == "candidate_expected_value_if_independent_probability_exists":
        return False, {}, ["p_resolve_yes_candidate"]
    else:
        return False, {}, [f"unsupported_template:{kind}"]
    values = {key: value for key, value in values.items() if value is not None}
    return bool(values), values, []


def build_formula_execution_rows(variants: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    execution_rows: list[dict[str, Any]] = []
    provisional_rows: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    compute_index = 0
    for variant in variants:
        if variant.get("exact_candidate_compute_eligible_flag"):
            lane = "EXACT_QKU_FORMULA"
        elif variant.get("provisional_compute_eligible_flag") or variant.get("template_id") == "candidate_expected_value_if_independent_probability_exists":
            lane = "PROVISIONAL_DATA_CONSUMER"
        else:
            continue
        compute_index += 1
        executed, computed_values, missing_inputs = _compute(variant)
        independent_missing = "p_resolve_yes_candidate" in missing_inputs or variant.get("template_id") != "candidate_expected_value_if_independent_probability_exists"
        classification = classify_execution(
            str(variant.get("template_id")),
            computed_values,
            independent_probability_missing=independent_missing,
        )
        compute_id = f"gfp2r_compute_{compute_index:05d}"
        receipt_ref = f"formula_execution_receipt::{compute_id}" if executed else None
        base = {
            "compute_row_id": compute_id,
            "compute_lane": lane,
            "qku_id": variant.get("qku_id"),
            "formula_id": variant.get("formula_id"),
            "formula_variant_id": variant.get("formula_variant_id"),
            "candidate_id": variant.get("candidate_id"),
            "mapping_row_id": variant.get("mapping_row_id"),
            "formula_expression_ref": variant.get("formula_expression_canonical"),
            "formula_version_ref": "PR168-GFP2R-v3.0",
            "formula_input_refs": variant.get("available_formula_inputs", []),
            "DATA1A_allowed_data_family_refs": variant.get("DATA1A_allowed_data_family_refs", []),
            "DATA1_snapshot_refs": variant.get("DATA1_snapshot_refs", []),
            "DATA1_feature_refs": variant.get("DATA1_feature_refs", []),
            "data_authority_class": "DATA1A_PUBLIC_CANDIDATE_DATA_NON_PROOF",
            "candidate_only_flag": True,
            "provisional_flag": lane == "PROVISIONAL_DATA_CONSUMER",
            "accepted_truth_flag": False,
            "source_evidence_acceptance_required_flag": True,
            "formula_executed_flag": executed,
            "formula_execution_receipt_ref": receipt_ref,
            "input_units": variant.get("input_units", {}),
            "unit_normalization_refs": variant.get("input_unit_normalization_refs", []),
            "computed_values": computed_values,
            "candidate_output_classification": classification,
            "proof_authority_class": "PROVISIONAL_DATA_CONSUMER_NON_PROOF"
            if lane == "PROVISIONAL_DATA_CONSUMER"
            else "CANDIDATE_ONLY_NON_PROOF",
            "real_positive_allowed_flag": False,
            "real_negative_allowed_flag": False,
            "historical_full_book_assumption_used_flag": False,
            "historical_full_book_forbidden_violation_flag": False,
            "market_implied_probability_used_flag": variant.get("template_id") == "market_implied_probability_baseline",
            "independent_probability_source_ref": None,
            "independent_probability_missing_flag": True,
            "repair_route_if_not_executed": "BIND_INDEPENDENT_PROBABILITY_MODEL"
            if "p_resolve_yes_candidate" in missing_inputs
            else ("REPAIR_REQUIRED_MISSING_FORMULA_INPUT" if missing_inputs else None),
            "downstream_RP2_ref": "PR168_GFP2R_To_PR168_RP2_CandidateFormulaRecomputeRows",
            "downstream_RANK2_ref": "PR168_GFP2R_To_PR168_RANK2_CandidateRankingRows",
            "venue": variant.get("venue"),
            "side": variant.get("side"),
            "market_id_or_token_id": variant.get("market_id_or_token_id"),
            **route_defaults(
                "execution",
                data1_refs=data1_report_refs(),
                data1a_refs=data1a_report_refs(),
                formula_refs=[str(variant.get("formula_id"))],
                formula_variant_refs=[str(variant.get("formula_variant_id"))],
                numeric_evidence_refs=[f"numeric_evidence::{compute_id}"] if executed else [],
                upstream_refs=[str(variant.get("formula_variant_id")), str(variant.get("mapping_row_id"))],
                computed_from_refs=variant.get("DATA1_snapshot_refs", []),
            ),
        }
        execution_rows.append(base)
        if lane == "PROVISIONAL_DATA_CONSUMER":
            provisional_rows.append(base)
        if executed:
            numeric_rows.append(
                {
                    "numeric_evidence_row_id": f"numeric_evidence::{compute_id}",
                    "compute_row_id": compute_id,
                    "formula_variant_id": variant.get("formula_variant_id"),
                    "computed_values": computed_values,
                    "candidate_output_classification": classification,
                    "proof_authority_class": base["proof_authority_class"],
                    "candidate_only_flag": True,
                    "provisional_flag": base["provisional_flag"],
                    **route_defaults(
                        "execution",
                        data1_refs=data1_report_refs(),
                        data1a_refs=data1a_report_refs(),
                        formula_variant_refs=[str(variant.get("formula_variant_id"))],
                        upstream_refs=[compute_id],
                        computed_from_refs=variant.get("DATA1_snapshot_refs", []),
                    ),
                }
            )
        if executed and any(key in computed_values for key in ("break_even_probability_after_costs", "required_probability_edge", "market_implied_probability")):
            threshold_rows.append(
                {
                    "break_even_row_id": f"break_even::{compute_id}",
                    "compute_row_id": compute_id,
                    "formula_variant_id": variant.get("formula_variant_id"),
                    "market_implied_probability": computed_values.get("market_implied_probability"),
                    "break_even_probability_after_costs": computed_values.get("break_even_probability_after_costs"),
                    "required_probability_edge": computed_values.get("required_probability_edge"),
                    "independent_probability_missing_flag": True,
                    "market_implied_probability_as_alpha_proof_flag": False,
                    "candidate_output_classification": classification,
                    **route_defaults(
                        "risk",
                        data1_refs=data1_report_refs(),
                        data1a_refs=data1a_report_refs(),
                        formula_variant_refs=[str(variant.get("formula_variant_id"))],
                        numeric_evidence_refs=[f"numeric_evidence::{compute_id}"],
                        upstream_refs=[compute_id],
                    ),
                }
            )
    return execution_rows, provisional_rows, numeric_rows, threshold_rows
