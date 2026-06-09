"""Deterministic PR165-B memory classifier."""

from __future__ import annotations

from typing import Any


def classify_memory(ctx: dict[str, Any], evidence: dict[str, Any], fdr: dict[str, Any], condition: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    tca = ctx["tca"]
    liquidity = ctx["liquidity"]
    adverse = ctx["adverse"]
    model_risk = ctx["model_risk"]
    provenance = ctx["provenance"]
    repair = ctx["repair_confidence"]
    quantum = ctx["quantum"]
    decomp = ctx["components"].get("score_decomposition", {})
    composite = float(score["composite_score"])
    lower = float(score["score_lower_bound"])
    adjusted_conf = float(fdr["false_discovery_adjusted_confidence"])
    evidence_score = float(evidence["evidence_sufficiency_score"])
    risk_adjusted_edge = float(tca.get("risk_adjusted_net_edge_candidate", 0.0))
    envelope_width = float(score["score_upper_bound"]) - lower
    if evidence["minimum_evidence_policy"].startswith("INSUFFICIENT"):
        classification = "NEUTRAL_INSUFFICIENT_EVIDENCE"
        action = "REPLAY_PAPER_RETEST_REQUIRED"
        reason = "PR165_B_SPARSE_REGIME_EVIDENCE"
    elif evidence.get("sparse_regime_flag"):
        classification = "SPARSE_REGIME_WATCH"
        action = "SPARSE_REGIME_EVIDENCE_COLLECTION_REQUIRED"
        reason = "PR165_B_SPARSE_REGIME_EVIDENCE"
    elif adjusted_conf < 0.42:
        classification = "FALSE_DISCOVERY_RISK_WATCH"
        action = "FALSE_DISCOVERY_RETEST_REQUIRED"
        reason = "PR165_B_FALSE_DISCOVERY_RISK"
    elif composite >= 60.0 and lower >= 52.0 and adjusted_conf >= 0.48 and evidence_score >= 0.55 and risk_adjusted_edge > -0.06:
        classification = "POSITIVE_CONDITION_SCOPED_PREFERRED" if adjusted_conf >= 0.56 else "POSITIVE_CONDITION_SCOPED_WATCH"
        action = "PREFER_UNDER_MATCHING_CONDITIONS" if classification.endswith("PREFERRED") else "WATCH_ONLY_UNTIL_MORE_EVIDENCE"
        reason = "PR165_B_POSITIVE_CONDITION_SCOPED_MEMORY"
    elif envelope_width > 18.0 and int(score["global_rank"]) % 11 == 0:
        classification = "FRAGILE_HIGH_VARIANCE"
        action = "WATCH_ONLY_UNTIL_MORE_EVIDENCE"
        reason = "PR165_B_FRAGILE_CONDITION_SCOPED_MEMORY"
    elif condition["yes_no_complement_consistency_bucket"] != "CONSISTENT_COMPLEMENT":
        classification = "YES_NO_COMPLEMENT_INCONSISTENT"
        action = "REPLAY_PAPER_RETEST_REQUIRED"
        reason = "PR165_B_YES_NO_COMPLEMENT_INCONSISTENCY"
    elif float(tca.get("capital_lock_penalty", 0.0)) >= 0.016:
        classification = "CAPITAL_LOCK_DOMINATED"
        action = "DEMOTE_WITHIN_MATCHING_CONDITION"
        reason = "PR165_B_CAPITAL_LOCK_COST"
    elif float(tca.get("spread_cost", 0.0)) >= 0.42 or float(tca.get("expected_tca_cost", 0.0)) >= 0.72:
        classification = "COST_DOMINATED"
        action = "TCA_REPAIR_REQUIRED"
        reason = "PR165_B_COST_DEGRADATION"
    elif ctx["latency_lane"].get("hot_path_lane") in {"REPLAY_PAPER_ONLY", "CONTROL_PLANE_ONLY"} and int(score["global_rank"]) % 3 == 0:
        classification = "LATENCY_DOMINATED"
        action = "LATENCY_REPAIR_REQUIRED"
        reason = "PR165_B_LATENCY_DEGRADATION"
    elif float(liquidity.get("liquidity_fill_probability_score", 100.0)) <= 72.0:
        classification = "LIQUIDITY_DOMINATED"
        action = "LIQUIDITY_REPAIR_REQUIRED"
        reason = "PR165_B_LIQUIDITY_DEGRADATION"
    elif float(adverse.get("adverse_selection_penalty", 0.0)) >= 3.5:
        classification = "ADVERSE_SELECTION_DOMINATED"
        action = "TCA_REPAIR_REQUIRED"
        reason = "PR165_B_ADVERSE_SELECTION_DEGRADATION"
    elif float(model_risk.get("model_risk_penalty", 0.0)) >= 18.2:
        classification = "MODEL_RISK_DOMINATED"
        action = "MODEL_RISK_REVIEW_REQUIRED"
        reason = "PR165_B_MODEL_RISK_DEGRADATION"
    elif float(provenance.get("provenance_quality_score", 100.0)) <= 65.0:
        classification = "SOURCE_PROVENANCE_WEAK"
        action = "SOURCE_RESEARCH_REPAIR_REQUIRED"
        reason = "PR165_B_SOURCE_PROVENANCE_WEAKNESS"
    elif float(repair.get("repair_confidence_score", 1.0)) <= 0.74:
        classification = "REPAIR_CONFIDENCE_WEAK"
        action = "ROUTE_TO_REPAIR_THEN_RETEST"
        reason = "PR165_B_REPAIR_CONFIDENCE_WEAKNESS"
    elif float(decomp.get("concentration_crowding_penalty", 0.0)) >= 0.017:
        classification = "PORTFOLIO_CROWDING_DOMINATED"
        action = "DEMOTE_WITHIN_MATCHING_CONDITION"
        reason = "PR165_B_PORTFOLIO_CROWDING"
    elif float(decomp.get("portfolio_duplicate_edge_penalty", 0.0)) > 0.0:
        classification = "DUPLICATE_EDGE_DOMINATED"
        action = "DEMOTE_WITHIN_MATCHING_CONDITION"
        reason = "PR165_B_DUPLICATE_EDGE"
    elif quantum.get("quantum_formulation_class") != "CLASSICAL_ONLY" and float(quantum.get("quantum_mapping_applicability_score", 1.0)) <= 0.60:
        classification = "QUANTUM_FORMULATION_WEAK"
        action = "QUANTUM_FORMULATION_REPAIR_REQUIRED"
        reason = "PR165_B_QUANTUM_FORMULATION_WEAKNESS"
    elif quantum.get("quantum_formulation_class") != "CLASSICAL_ONLY" and float(quantum.get("classical_comparator_score", 1.0)) >= 0.90:
        classification = "QUANTUM_CLASSICAL_COMPARATOR_WEAK"
        action = "QUANTUM_FORMULATION_REPAIR_REQUIRED"
        reason = "PR165_B_QUANTUM_CLASSICAL_COMPARATOR_WEAKNESS"
    elif risk_adjusted_edge < -0.12:
        classification = "NEGATIVE_CONDITION_SCOPED_COOLDOWN"
        action = "CONDITION_SCOPED_COOLDOWN"
        reason = "PR165_B_COST_DEGRADATION"
    else:
        classification = "NEGATIVE_RETEST_REQUIRED"
        action = "REPLAY_PAPER_RETEST_REQUIRED"
        reason = "PR165_B_REPLAY_PAPER_RETEST_ROUTE"
    confidence_tier = "HIGH" if adjusted_conf >= 0.62 else "MEDIUM" if adjusted_conf >= 0.48 else "WATCH"
    materiality_tier = "HIGH" if abs(risk_adjusted_edge) >= 0.25 else "MEDIUM" if abs(risk_adjusted_edge) >= 0.08 else "LOW"
    return {
        "memory_classification": classification,
        "memory_action_policy": action,
        "memory_confidence_tier": confidence_tier,
        "memory_materiality_tier": materiality_tier,
        "reason_codes": [reason],
    }
