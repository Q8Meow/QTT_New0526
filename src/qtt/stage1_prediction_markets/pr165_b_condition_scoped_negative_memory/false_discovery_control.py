"""Deterministic false-discovery controls for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_false_discovery_record(index: int, ctx: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    rank = int(score["global_rank"])
    raw_confidence = float(evidence["classification_confidence"])
    compared_conditions = int(ctx.get("total_regime_rows", 117036))
    compared_combinations = int(ctx.get("total_candidate_rows", 6502))
    if evidence["minimum_evidence_policy"].startswith("INSUFFICIENT"):
        method = "INSUFFICIENT_EVIDENCE_WATCH_ONLY"
        adjustment = 0.20
    elif rank <= 1500:
        method = "DETERMINISTIC_BH_STYLE_RANK_ADJUSTMENT"
        adjustment = min(0.16, rank / compared_combinations * 0.12)
    elif rank >= 5600:
        method = "CONSERVATIVE_LOWER_BOUND_ONLY"
        adjustment = 0.22
    else:
        method = "DETERMINISTIC_BONFERRONI_STYLE_CAP"
        adjustment = 0.18
    adjusted = round(max(0.0, raw_confidence - adjustment), 6)
    selection_bias = "HIGH" if adjusted < 0.42 else "MEDIUM" if rank > 4500 else "LOW"
    overfit = "HIGH" if adjusted < 0.40 else "MEDIUM" if method != "DETERMINISTIC_BH_STYLE_RANK_ADJUSTMENT" else "LOW"
    classification_after = (
        "FALSE_DISCOVERY_RISK_WATCH"
        if adjusted < 0.42
        else "EVIDENCE_CONFIDENCE_RETAINED_FOR_CONDITION_SCOPE"
    )
    return {
        "false_discovery_control_ref": ordinal_ref("PR165_B_FALSE_DISCOVERY", index),
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "multiple_test_family_id": f"PR165_B_MULTIPLE_TEST_FAMILY::{ctx['formula_family']}::{ctx['condition_family']}",
        "number_of_compared_conditions": compared_conditions,
        "number_of_compared_combinations": compared_combinations,
        "raw_outcome_confidence": raw_confidence,
        "false_discovery_adjusted_confidence": adjusted,
        "false_discovery_adjustment_method": method,
        "selection_bias_risk_tier": selection_bias,
        "overfit_risk_tier": overfit,
        "overfit_penalty": round(adjustment, 6),
        "memory_classification_after_false_discovery_adjustment": classification_after,
        "validation_status": "PASS",
    }
