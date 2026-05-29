"""Quantum formula-template registry construction."""

from __future__ import annotations

from . import constants as c


def build_formula_templates() -> list[dict[str, object]]:
    expressions = {
        "QUBO_OBJECTIVE_TEMPLATE": "minimize x^T Q x + linear_terms + constant_terms",
        "ISING_OBJECTIVE_TEMPLATE": "minimize sum_i h_i z_i + sum_ij J_ij z_i z_j",
        "QAOA_CANDIDATE_TEMPLATE": "minimize <psi(beta,gamma)|C_qubo_or_ising|psi(beta,gamma)>",
        "VQE_CANDIDATE_TEMPLATE": "minimize <psi(theta)|H_objective|psi(theta)>",
        "ANNEALING_CANDIDATE_TEMPLATE": "minimize energy(binary_variables, constraints, schedule)",
        "HYBRID_COMPARE_THEN_SELECT_TEMPLATE": "select argmin(classical_score, quantum_candidate_score) after replay/paper comparison",
        "QUANTUM_TIEBREAKER_TEMPLATE": "apply quantum_priority_policy when classical score delta <= near_tie_threshold",
    }
    return [
        {
            "formula_template_id": f"PR161A_FORMULA_TEMPLATE__{family}",
            "formula_family": family,
            "mathematical_expression": expressions[family],
            "objective_terms": ["expected_value_candidate", "risk_adjustment_candidate", "cost_candidate"],
            "constraint_terms": ["budget", "exposure", "latency", "liquidity"],
            "penalty_terms": ["risk_penalty", "transaction_cost_penalty", "latency_penalty"],
            "variable_domain": "BINARY_0_1" if family != "ISING_OBJECTIVE_TEMPLATE" else "SPIN_MINUS_ONE_PLUS_ONE",
            "mapping_to_atomicrows_roles": ["selection", "risk", "capital", "latency", "optimizer"],
            "mapping_to_pr154_targets": ["PR154_VALUE_STATE_TARGETS"],
            "mapping_to_strategy_class": "PREDICTION_MARKET_OPTIMIZER_RESEARCH",
            "mapping_to_market_type": "PREDICTION_MARKETS_GENERAL",
            "mapping_to_platform_scope": "KALSHI_POLYMARKET_FORECASTEX_IBKR_GENERAL",
            "quantum_applicability_class": "QUANTUM_FORWARD_CANDIDATE",
            "classical_baseline_formula_id": "PR161A_CLASSICAL_BASELINE_GREEDY_LINEAR_COST",
            "replay_paper_route_id": f"PR161A_QUANTUM_REPLAY_ROUTE__{family}",
            "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "default_parameter_profile_id": f"PR161A_DEFAULT_PROFILE__{family.split('_')[0]}",
            "optimizer_arbitration_profile_id": "PR161A_HYBRID_ARBITRATION_PROFILE",
            "source_or_basis": "QTT_PR161A_OWNER_APPROVED_QUANTUM_CANDIDATE_DEFAULT",
            "candidate_status": "CANDIDATE_READY_FOR_REPLAY_PAPER_DESCRIPTOR",
        }
        for family in c.QUANTUM_FORMULA_TEMPLATE_FAMILIES
    ]

