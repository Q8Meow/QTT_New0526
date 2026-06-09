"""PR165 score model constants materialized into configuration artifacts."""

from __future__ import annotations


SCORE_MODEL_ID = "PR165_SCORE_MODEL_V1"
SCORE_FORMULA_VERSION = "PR165_FORMULA_V1"
SCORE_RANGE = "0_to_100"
CONFIDENCE_RANGE = "0_to_1"
FIXED_SEED_POLICY = "NO_RANDOM_BOOTSTRAP_DETERMINISTIC_CONSERVATIVE_ENVELOPE"

COMPONENT_WEIGHTS = {
    "expected_value_score": 1.0,
    "probability_calibration_score": 0.6,
    "replay_score": 0.45,
    "paper_score": 0.45,
    "replay_paper_alignment_score": 0.7,
    "tca_adjusted_edge_score": 1.0,
    "implementation_shortfall_score": 0.45,
    "scenario_stress_robustness_score": 0.55,
    "walk_forward_holdout_score": 0.45,
    "liquidity_fill_probability_score": 0.65,
    "maker_taker_route_score": 0.5,
    "automated_trading_control_coverage_score": 0.55,
    "repair_confidence_score": 0.45,
    "data_quality_score": 0.55,
    "provenance_quality_score": 0.55,
    "quantum_priority_boost": 0.2,
    "divergence_penalty": -0.65,
    "latency_penalty": -0.6,
    "adverse_selection_penalty": -0.55,
    "model_risk_penalty": -0.85,
    "source_candidate_penalty": -0.4,
    "complexity_penalty": -0.35,
    "operational_burden_penalty": -0.35,
    "portfolio_duplicate_edge_penalty": -0.45,
    "concentration_crowding_penalty": -0.45,
}

PENALTY_CAPS = {
    "latency_penalty": 25.0,
    "adverse_selection_penalty": 22.0,
    "model_risk_penalty": 28.0,
    "source_candidate_penalty": 16.0,
    "complexity_penalty": 14.0,
    "operational_burden_penalty": 12.0,
    "portfolio_duplicate_edge_penalty": 12.0,
    "concentration_crowding_penalty": 12.0,
    "divergence_penalty": 24.0,
}

NORMALIZATION_POLICY = {
    "score_range": SCORE_RANGE,
    "confidence_range": CONFIDENCE_RANGE,
    "clip_inputs_to_declared_bounds": True,
    "round_numeric_outputs_to_6_decimals": True,
    "stable_deterministic_sorting_required": True,
    "random_unseeded_behavior_allowed": False,
    "opaque_rank_only_output_allowed": False,
}
