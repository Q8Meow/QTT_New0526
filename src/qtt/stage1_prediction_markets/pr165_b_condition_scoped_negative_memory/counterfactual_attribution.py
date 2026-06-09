"""Counterfactual attribution rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_counterfactual_attribution_record(
    index: int,
    ctx: dict[str, Any],
    condition_id: str,
    combination_id: str,
    outcome_attribution: dict[str, Any],
) -> dict[str, Any]:
    decomp = ctx["components"].get("score_decomposition", {})
    tca = ctx["tca"]
    raw_score = float(decomp.get("expected_value_score", ctx["score"].get("composite_score", 0.0)))
    score_after_tca = float(tca.get("tca_adjusted_edge_score", raw_score))
    score_after_latency = max(0.0, score_after_tca - float(decomp.get("latency_penalty", 0.0)))
    score_after_liquidity = min(score_after_latency, float(ctx["liquidity"].get("liquidity_fill_probability_score", score_after_latency)))
    score_after_model_risk = max(0.0, score_after_liquidity - float(ctx["model_risk"].get("model_risk_penalty", 0.0)))
    score_after_source = max(0.0, score_after_model_risk - float(ctx["provenance"].get("source_candidate_penalty", 0.0)))
    score_after_crowding = max(0.0, score_after_source - float(decomp.get("concentration_crowding_penalty", 0.0)) * 10.0)
    score_after_quantum = score_after_crowding + float(ctx["quantum_priority"].get("quantum_priority_boost", 0.0))
    dominant = outcome_attribution["dominant_attribution_family"]
    repair_route = {
        "fees": "TCA_REPAIR_REQUIRED",
        "spread": "TCA_REPAIR_REQUIRED",
        "slippage": "TCA_REPAIR_REQUIRED",
        "latency_adverse_selection": "LATENCY_REPAIR_REQUIRED",
        "queue_nonfill": "LIQUIDITY_REPAIR_REQUIRED",
        "liquidity_depth": "LIQUIDITY_REPAIR_REQUIRED",
        "model_risk": "MODEL_RISK_REVIEW_REQUIRED",
        "source_provenance": "SOURCE_RESEARCH_REPAIR_REQUIRED",
        "quantum_objective_gap": "QUANTUM_FORMULATION_REPAIR_REQUIRED",
        "quantum_classical_comparator_gap": "QUANTUM_FORMULATION_REPAIR_REQUIRED",
    }.get(dominant, "REPLAY_PAPER_RETEST_REQUIRED")
    return {
        "counterfactual_attribution_ref": ordinal_ref("PR165_B_COUNTERFACTUAL_ATTRIBUTION", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "outcome_attribution_ref": outcome_attribution["outcome_attribution_ref"],
        "raw_score_before_TCA": round(raw_score, 6),
        "score_after_TCA": round(score_after_tca, 6),
        "score_after_latency": round(score_after_latency, 6),
        "score_after_liquidity_fill": round(score_after_liquidity, 6),
        "score_after_model_risk": round(score_after_model_risk, 6),
        "score_after_source_penalty": round(score_after_source, 6),
        "score_after_portfolio_crowding": round(score_after_crowding, 6),
        "score_after_quantum_adjustment": round(score_after_quantum, 6),
        "dominant_degradation_driver": dominant,
        "counterfactual_best_repair_route": repair_route,
        "validation_status": "PASS",
    }
