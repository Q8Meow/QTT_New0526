"""Score policies for PR166-SM3."""

from __future__ import annotations

SCORE_COMPONENT_WEIGHTS: dict[str, float] = {
    "normalized_retested_net_edge_after_costs": 0.18,
    "edge_lower_confidence_bound": 0.13,
    "holdout_robustness_score": 0.10,
    "conversion_proof_strength": 0.08,
    "fill_realism_score": 0.08,
    "probability_calibration_score": 0.07,
    "tca_quality_score": 0.07,
    "before_after_uplift_score": 0.06,
    "capacity_score": 0.05,
    "marginal_utility_score": 0.05,
    "quantum_structural_readiness_score": 0.05,
    "champion_challenger_stability_score": 0.04,
    "regime_memory_consistency_score": 0.04,
    "false_discovery_risk_adjustment": -0.06,
    "overfit_risk_adjustment": -0.06,
    "residual_cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.03,
    "liquidity_drag_ratio": -0.03,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "settlement_sensitivity_score": -0.02,
    "no_fill_risk_score": -0.02,
    "rank_instability_adjustment": -0.02,
}

QUANTUM_COMBO_WEIGHTS: dict[str, float] = {
    "objective_completeness": 0.20,
    "variable_domain_completeness": 0.15,
    "constraint_penalty_quality": 0.13,
    "coefficient_materialization_quality": 0.12,
    "model_family_fit": 0.10,
    "classical_comparator_strength": 0.10,
    "latency_budget_fit": 0.08,
    "fallback_safety": 0.07,
    "downstream_q_route_clarity": 0.05,
}


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def round6(value: float) -> float:
    return round(float(value), 6)


def score_from_components(components: dict[str, float]) -> float:
    raw = sum(components.get(name, 0.0) * weight for name, weight in SCORE_COMPONENT_WEIGHTS.items())
    return round6(clamp(raw, -1.0, 1.0))


def quantum_combo_score(components: dict[str, float]) -> float:
    raw = sum(components.get(name, 0.0) * weight for name, weight in QUANTUM_COMBO_WEIGHTS.items())
    return round6(clamp(raw))
