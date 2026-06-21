#!/usr/bin/env python3
"""Quantum structural readiness classification for PR168-GFP2."""

from __future__ import annotations

from typing import Any


def quantum_readiness_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in universe_rows:
        quantum = row["quantum_objective_state"] != "NOT_QUANTUM_OBJECTIVE_ROW"
        rows.append(
            {
                "canonical_row_key": row["canonical_row_key"],
                "qku_id": row["qku_id"],
                "formula_id": row["formula_id"],
                "objective_exists": quantum,
                "objective_type": "portfolio_stack_selection_quadratic" if quantum else "not_quantum_forward",
                "objective_expression_ref": row["formula_expression_ref"] if quantum else None,
                "variables_exist": False if quantum else None,
                "variable_domains": "BINARY_PENDING_BINDING" if quantum else None,
                "binary_variable_count": 0,
                "integer_variable_count": 0,
                "continuous_variable_count": 0,
                "linear_coefficients_exist": False,
                "quadratic_coefficients_exist": False,
                "higher_order_terms_exist": False,
                "constraints_exist": False,
                "constraint_types": [],
                "constraint_rhs_refs": [],
                "penalty_scaling_exists": False,
                "penalty_scaling_source_or_gap": "PR168_GFP2_QuantumPenaltyScalingGapQueue.report.json" if quantum else "NOT_APPLICABLE",
                "qubo_map_exists": False,
                "bqm_map_exists": False,
                "cqm_map_exists": False,
                "ising_map_exists": False,
                "qiskit_quadraticprogram_map_exists": False,
                "qaoa_candidate_map_exists": False,
                "vqe_candidate_map_exists": False,
                "interpret_back_map_exists": False,
                "classical_fallback_exists": True,
                "classical_comparator_exists": True,
                "constraint_satisfaction_check_exists": False,
                "objective_value_check_exists": False,
                "backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                "repair_route_if_missing": "PR168_GFP2_QUBO_BQM_CQM_Ising_QuadraticProgramMappingQueue.report.json"
                if quantum
                else "NOT_APPLICABLE",
                "structural_readiness_state": "QUANTUM_STRUCTURAL_GAP_ROUTED" if quantum else "NON_QUANTUM_ROW",
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2", "PR162E"],
                "agent_owner": "Quantum Optimizer Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def quantum_portfolio_objective_seed_rows() -> list[dict[str, Any]]:
    return [
        {
            "objective_seed_id": "PR168_GFP2_QUANTUM_PORTFOLIO_STACK_SELECTION_OBJECTIVE",
            "decision_variables": ["x_i", "s_i_or_b_i_optional_when_structurally_valid"],
            "objective_expression": "maximize sum_i alpha_i*x_i - sum_i cost_i*x_i - sum_i capacity_penalty_i*x_i - sum_i fdr_penalty_i*x_i - sum_i latency_penalty_i*x_i - sum_ij correlation_penalty_ij*x_i*x_j - sum_ij concentration_penalty_ij*x_i*x_j",
            "constraints": [
                "total_risk_budget <= risk_budget_limit",
                "total_capacity_usage <= capacity_limit",
                "per_event_family_exposure <= event_family_limit",
                "per_venue_exposure <= venue_limit",
                "no mutually exclusive YES/NO contradiction unless hedge semantics explicit",
                "no live execution authority",
            ],
            "qubo_bqm_allowed_when_penalty_scaled_flag": True,
            "cqm_or_quadraticprogram_required_for_explicit_constraints_flag": True,
            "penalty_scaling_gap_route": "PR168_GFP2_QuantumPenaltyScalingGapQueue.report.json",
            "classical_fallback_exists": True,
            "classical_comparator_exists": True,
            "backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "downstream_pr_refs": ["PR168-RANK2", "PR162E"],
            "agent_owner": "Quantum Optimizer Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
    ]
