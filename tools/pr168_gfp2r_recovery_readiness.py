#!/usr/bin/env python3
"""Negative/weak candidate recovery variant generation for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


RECOVERY_DIMENSIONS = [
    "side_flip_candidate",
    "order_policy_switch_candidate",
    "order_size_reduction_candidate",
    "entry_threshold_adjustment_candidate",
    "latency_bucket_adjustment_candidate",
    "spread_filter_candidate",
    "liquidity_filter_candidate",
    "fee_model_repair_candidate",
    "fill_model_repair_candidate",
    "probability_model_binding_candidate",
    "scenario_stress_repair_candidate",
    "regime_condition_reroute_candidate",
    "portfolio_cluster_reroute_candidate",
    "quantum_coefficient_repair_candidate",
    "no_trade_preferred_route",
]


def build_recovery_variant_rows(execution_rows: list[dict[str, Any]], stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    weak_rows = [
        row
        for row in execution_rows
        if row.get("independent_probability_missing_flag")
        or row.get("candidate_output_classification")
        in {"CANDIDATE_NO_TRADE_PREFERRED_NON_PROOF", "PROBABILITY_MODEL_REQUIRED_FOR_EDGE"}
    ]
    stack_by_compute = {stack["compute_row_id"]: stack for stack in stack_rows}
    index = 0
    for row in weak_rows:
        stack = stack_by_compute.get(row["compute_row_id"], {})
        for dimension in RECOVERY_DIMENSIONS[:5]:
            index += 1
            missing_probability_penalty = 5.0 if row.get("independent_probability_missing_flag") else 0.0
            score = round(
                3.0
                + (1.0 if stack else 0.0)
                + (0.5 if row.get("formula_executed_flag") else 0.0)
                - missing_probability_penalty,
                6,
            )
            rows.append(
                {
                    "recovery_variant_id": f"recovery_variant_{index:05d}",
                    "compute_row_id": row["compute_row_id"],
                    "candidate_stack_id": stack.get("candidate_stack_id"),
                    "formula_variant_id": row.get("formula_variant_id"),
                    "diagnosis_dimensions": [
                        "missing_independent_probability_model",
                        "market_implied_probability_uncalibrated",
                        "source_acceptance_required",
                        "historical_full_book_required_but_absent",
                        "overfit_fdr_uncontrolled",
                    ],
                    "recovery_variant_dimension": dimension,
                    "recovery_actions": [
                        "bind_independent_probability_model",
                        "route_to_RP2_fill_slippage_latency_recompute",
                        "route_to_no_trade_if_margin_insufficient",
                    ],
                    "candidate_output_classification": row.get("candidate_output_classification"),
                    "forced_positive_flag": False,
                    "real_positive_claim_allowed_flag": False,
                    "recovery_priority_score_non_proof": score,
                    "repair_route": "PR168_RP2_OR_RANK2_REPAIR_WITH_NO_POSITIVE_FORCING",
                    **route_defaults(
                        "risk",
                        data1_refs=data1_report_refs(),
                        data1a_refs=data1a_report_refs(),
                        formula_variant_refs=[str(row.get("formula_variant_id"))],
                        upstream_refs=[row["compute_row_id"]],
                    ),
                }
            )
    return rows
