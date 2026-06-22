#!/usr/bin/env python3
"""Quantum-forward structural candidate map for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_quantum_candidate_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, stack in enumerate(stack_rows, start=1):
        variable_id = f"x_{index}"
        quality = 1.0 if stack.get("candidate_output_classification") else 0.0
        gap_penalty = 1.0 if stack.get("candidate_execution_adjusted_edge") is None else 0.0
        rows.append(
            {
                "quantum_mapping_id": f"quantum_map::{stack['candidate_stack_id']}",
                "binary_variable_id": variable_id,
                "candidate_stack_ref": stack["candidate_stack_id"],
                "formula_variant_ref": stack.get("formula_variant_id"),
                "linear_coefficient_refs": {
                    "candidate_quality_i": quality,
                    "candidate_edge_seed_i": stack.get("candidate_execution_adjusted_edge"),
                    "downstream_unblock_i": 1.0,
                    "break_even_threshold_quality_i": 1.0 if stack.get("break_even_probability_after_costs") is not None else 0.0,
                    "formula_variant_diversity_value_i": 1.0,
                    "tca_cost_seed_i": abs(stack.get("candidate_no_trade_margin") or 0.0),
                    "latency_penalty_i": 0.1,
                    "capacity_gap_penalty_i": 0.1,
                    "fdr_penalty_i": 0.1,
                    "source_acceptance_gap_penalty_i": 1.0,
                    "probability_model_gap_penalty_i": gap_penalty,
                    "historical_full_book_gap_penalty_i": 1.0,
                    "duplicate_complexity_penalty_i": 0.0,
                },
                "quadratic_coefficient_refs": {
                    "event_family_concentration_penalty_ij": f"portfolio_cluster::{stack.get('market_id_or_token_id')}",
                    "same_market_contradiction_penalty_ij": f"same_market::{stack.get('market_id_or_token_id')}",
                },
                "constraint_refs": [
                    "per_venue_batch_count <= configured_candidate_limit",
                    "per_event_family_batch_count <= configured_candidate_limit",
                    "formula_equivalence_cluster_count <= configured_candidate_limit",
                    "no historical-full-book-dependent row without verified full-book source",
                    "no live execution authority",
                ],
                "penalty_scaling_source_or_gap": "MISSING_PENALTY_SCALING_SOURCE_USE_CQM_OR_QUADRATIC_PROGRAM",
                "coefficient_quality_state": "PARTIAL_SEED_FROM_CANDIDATE_COMPUTE_ROWS",
                "constraint_quality_state": "EXPLICIT_CONSTRAINT_SEED",
                "QUBO_ready_candidate_flag": False,
                "BQM_ready_candidate_flag": False,
                "CQM_ready_candidate_flag": True,
                "Ising_ready_candidate_flag": False,
                "QuadraticProgram_ready_candidate_flag": True,
                "interpret_back_map_exists": True,
                "classical_fallback_exists": True,
                "classical_comparator_exists": True,
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                "repair_route_if_missing": "PENALTY_SCALING_AND_COEFFICIENT_REVIEW_REQUIRED_BEFORE_QUBO_BQM",
                **route_defaults(
                    "quantum",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[str(stack.get("formula_variant_id"))],
                    upstream_refs=[stack["candidate_stack_id"]],
                ),
            }
        )
    return rows
