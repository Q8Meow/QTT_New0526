#!/usr/bin/env python3
"""Quantum-forward coefficient feature surface for DATA1, with no backend execution."""

from __future__ import annotations

from tools.pr168_data1_config import authority_flags, route_defaults


def build_quantum_surface(priority_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    rows = []
    for index, priority in enumerate(priority_rows, start=1):
        variable = f"x_{index}"
        rows.append(
            {
                "quantum_feature_vector_id": f"pr168_data1_quantum_feature_vector_{index:04d}",
                "candidate_stack_binary_variable_universe": [variable],
                "alpha_coefficient_data_source": priority["feature_refs"],
                "cost_coefficient_data_source": priority["feature_refs"],
                "capacity_constraint_data_source": priority["feature_refs"],
                "liquidity_constraint_data_source": priority["feature_refs"],
                "correlation_penalty_data_source": ["event_family_concentration_penalty_seed"],
                "concentration_penalty_data_source": ["per_event_family_batch_size"],
                "latency_penalty_data_source": ["data_staleness_penalty_seed"],
                "fdr_penalty_data_source": ["fdr_family_id"],
                "no_trade_constraint_data_source": ["NO_TRADE_BASELINE_PERMANENT_COMPETITOR"],
                "historical_full_book_quality_coefficient": 0.0,
                "forward_l2_capture_quality_coefficient": 1.0,
                "price_history_quality_coefficient": 1.0 if priority["feature_refs"] else 0.0,
                "penalty_scaling_gap_flag": True,
                "classical_fallback_required_flag": True,
                "classical_comparator_required_flag": True,
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                "objective_seed": (
                    "maximize sum_i data_quality_i*x_i + historical_full_book_quality_i*x_i + "
                    "forward_l2_quality_i*x_i + expected_downstream_unblock_i*x_i - staleness_penalty_i*x_i "
                    "- capacity_gap_penalty_i*x_i - source_acceptance_gap_penalty_i*x_i "
                    "- event_family_concentration_penalty_ij*x_i*x_j"
                ),
                "constraints": [
                    "per_venue_batch_size <= configured_limit",
                    "per_event_family_batch_size <= configured_limit",
                    "no duplicate market/outcome rows unless needed for YES/NO pairing",
                    "no candidate without upstream snapshot or replay refs",
                    "no live execution authority",
                ],
                "mapping_readiness": "CQM_OR_QUADRATIC_PROGRAM_PREFERRED_UNTIL_PENALTY_SCALING_GAPS_RESOLVED",
                "created_at_utc": now_utc,
                **route_defaults("quantum"),
                **authority_flags(),
            }
        )
    return rows
