"""Quantum replay/paper descriptor construction."""

from __future__ import annotations

from . import constants as c


def build_quantum_replay_descriptors(
    profiles: list[dict[str, object]],
    strategies: list[dict[str, object]],
) -> list[dict[str, object]]:
    descriptors: list[dict[str, object]] = []
    for index, profile in enumerate(profiles):
        strategy = strategies[index % len(strategies)]
        comparison = _comparison_for(str(profile["quantum_profile_type"]))
        descriptors.append(
            {
                "experiment_descriptor_id": f"PR161A_QEXP__{index+1:04d}",
                "quantum_candidate_id": profile["quantum_candidate_id"],
                "strategy_candidate_id": strategy["strategy_candidate_id"],
                "classical_baseline_formula_id": profile["classical_baseline_formula_id"],
                "replay_lane_required_flag": True,
                "paper_lane_required_flag": True,
                "comparison_type": comparison,
                "objective_metric_candidates": ["net_edge_candidate", "fill_adjusted_value_candidate"],
                "risk_metric_candidates": ["drawdown", "exposure", "tail_loss"],
                "latency_metric_candidates": ["decision_latency", "route_latency"],
                "cost_metric_candidates": ["fees", "slippage", "transaction_cost_penalty"],
                "candidate_parameter_grid": profile["default_parameter_profile_id"],
                "holdout_or_scenario_class": "HISTORICAL_REPLAY_AND_SYNTHETIC_PAPER_SCENARIOS",
                "promotion_candidate_after_success_flag": True,
                "owner_review_after_success_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return descriptors


def _comparison_for(profile_type: str) -> str:
    if profile_type.startswith("QUBO"):
        return "CLASSICAL_BASELINE_VS_QUBO"
    if profile_type.startswith("ISING"):
        return "CLASSICAL_BASELINE_VS_ISING"
    if profile_type.startswith("QAOA"):
        return "CLASSICAL_BASELINE_VS_QAOA"
    if profile_type.startswith("VQE"):
        return "CLASSICAL_BASELINE_VS_VQE"
    if profile_type.startswith(("ANNEALING", "QUANTUM_INSPIRED")):
        return "CLASSICAL_BASELINE_VS_ANNEALING"
    if profile_type.startswith("HYBRID"):
        return "CLASSICAL_BASELINE_VS_HYBRID_ARBITRATION"
    if profile_type.startswith("OWNER"):
        return "QUANTUM_PRIORITY_POLICY_SENSITIVITY_TEST"
    return c.QUANTUM_COMPARISON_TYPES[0]

