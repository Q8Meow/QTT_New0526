"""Scenario outcome matrix rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def outcome_sign_for(classification: str) -> str:
    if classification.startswith("POSITIVE"):
        return "POSITIVE"
    if classification == "NEUTRAL_INSUFFICIENT_EVIDENCE":
        return "INSUFFICIENT_EVIDENCE"
    if "WATCH" in classification or classification == "FRAGILE_HIGH_VARIANCE":
        return "MIXED"
    return "NEGATIVE"


def build_scenario_outcome_record(
    index: int,
    ctx: dict[str, Any],
    condition: dict[str, Any],
    combination: dict[str, Any],
    asof: dict[str, Any],
    evidence: dict[str, Any],
    fdr: dict[str, Any],
    classification: dict[str, Any],
) -> dict[str, Any]:
    score = ctx["score"]
    decomp = ctx["components"].get("score_decomposition", {})
    tca = ctx["tca"]
    outcome_sign = outcome_sign_for(classification["memory_classification"])
    return {
        "scenario_outcome_ref": ordinal_ref("PR165_B_SCENARIO_OUTCOME", index),
        "condition_fingerprint_id": condition["condition_fingerprint_id"],
        "combination_fingerprint_id": combination["combination_fingerprint_id"],
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "replay_result_ref": ctx["replay"].get("replay_score_ref", score["replay_paper_evidence_ref"]),
        "paper_result_ref": ctx["paper"].get("paper_score_ref", score["replay_paper_evidence_ref"]),
        "as_of_evidence_ref": asof["as_of_evidence_ref"],
        "leakage_audit_ref": asof["asof_leakage_audit_ref"],
        "replay_score": decomp.get("replay_score", ctx["replay"].get("replay_score", 0.0)),
        "paper_score": decomp.get("paper_score", ctx["paper"].get("paper_score", 0.0)),
        "replay_paper_alignment_score": decomp.get("replay_paper_alignment_score", ctx["alignment"].get("replay_paper_alignment_score", 0.0)),
        "divergence_score": 100.0 - float(ctx["divergence"].get("divergence_penalty", 0.0)),
        "expected_value_score": decomp.get("expected_value_score", ctx["expected_value"].get("expected_value_score", 0.0)),
        "TCA_adjusted_score": tca.get("tca_adjusted_edge_score", 0.0),
        "implementation_shortfall_score": ctx["implementation_shortfall"].get("implementation_shortfall_score", 0.0),
        "latency_adjusted_score": ctx["latency_score"].get("latency_adjusted_score", decomp.get("latency_adjusted_score", 0.0)),
        "liquidity_fill_score": ctx["liquidity"].get("liquidity_fill_probability_score", 0.0),
        "maker_taker_route_score": ctx["maker_taker"].get("maker_taker_route_score", decomp.get("maker_taker_route_score", 0.0)),
        "adverse_selection_penalty": ctx["adverse"].get("adverse_selection_penalty", 0.0),
        "model_risk_penalty": ctx["model_risk"].get("model_risk_penalty", 0.0),
        "quantum_priority_score": ctx["quantum_priority"].get("quantum_priority_boost", decomp.get("quantum_priority_boost", 0.0)),
        "quantum_mapping_applicability_score": ctx["quantum"].get("quantum_mapping_applicability_score", 0.0),
        "portfolio_duplicate_edge_penalty": decomp.get("portfolio_duplicate_edge_penalty", 0.0),
        "concentration_crowding_penalty": decomp.get("concentration_crowding_penalty", 0.0),
        "net_edge_candidate": tca.get("net_edge_candidate", 0.0),
        "risk_adjusted_net_edge_candidate": tca.get("risk_adjusted_net_edge_candidate", 0.0),
        "net_profit_candidate_non_live": round(float(tca.get("risk_adjusted_net_edge_candidate", 0.0)) * 100.0, 6),
        "max_drawdown_candidate_non_live": round((100.0 - float(decomp.get("drawdown_risk_component", 80.0))) / 100.0, 6),
        "stress_robustness_score": ctx["stress"].get("scenario_stress_robustness_score", decomp.get("scenario_stress_robustness_score", 0.0)),
        "evidence_sufficiency_score": evidence["evidence_sufficiency_score"],
        "false_discovery_adjusted_confidence": fdr["false_discovery_adjusted_confidence"],
        "outcome_sign": outcome_sign,
        "outcome_confidence": fdr["false_discovery_adjusted_confidence"],
        "outcome_materiality": classification["memory_materiality_tier"],
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "validation_status": "PASS",
    }
