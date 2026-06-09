"""Cooldown policy rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def cooldown_duration_for(classification: str) -> str:
    if classification == "STRUCTURAL_INVALIDITY_ARCHIVE_CANDIDATE":
        return "ARCHIVE_UNTIL_STRUCTURAL_REPAIR"
    if "REPAIR" in classification or classification in {"SOURCE_PROVENANCE_WEAK", "QUANTUM_FORMULATION_WEAK", "QUANTUM_CLASSICAL_COMPARATOR_WEAK"}:
        return "LONG_RETEST_AFTER_MATERIAL_FORMULA_OR_SOURCE_CHANGE"
    if classification in {"FRAGILE_HIGH_VARIANCE", "SPARSE_REGIME_WATCH", "FALSE_DISCOVERY_RISK_WATCH", "NEUTRAL_INSUFFICIENT_EVIDENCE"}:
        return "SHORT_RETEST_AFTER_NEW_PAPER_EVIDENCE"
    return "MEDIUM_RETEST_AFTER_REPAIR_OR_NEW_REGIME"


def build_cooldown_policy_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    memory_classification = classification["memory_classification"]
    duration = cooldown_duration_for(memory_classification)
    return {
        "cooldown_policy_ref": ordinal_ref("PR165_B_COOLDOWN_POLICY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": memory_classification,
        "memory_action_policy": classification["memory_action_policy"],
        "cooldown_required": duration != "NO_COOLDOWN",
        "cooldown_family": "SPARSE_OR_FALSE_DISCOVERY_RETEST_COOLDOWN" if "WATCH" in memory_classification or "INSUFFICIENT" in memory_classification else "COST_AND_SPREAD_COOLDOWN",
        "cooldown_duration_bucket": duration,
        "cooldown_start_ref": f"PR165_B_MEMORY_CLASSIFICATION::{ctx['score']['candidate_packet_id']}",
        "cooldown_end_condition": "NEW_REPLAY_OR_PAPER_EVIDENCE_OR_REPAIR_VERSION_UNDER_MATCHING_CONDITION",
        "retest_required": True,
        "retest_condition": "MATCHING_CONDITION_SCOPE_OR_EXPLICIT_REGIME_CHANGE",
        "retest_trigger": "NEW_PAPER_EVIDENCE" if duration.startswith("SHORT") else "REGIME_CHANGED",
        "retest_minimum_new_evidence": 12,
        "repair_required_before_retest": classification["memory_action_policy"].endswith("REPAIR_REQUIRED") or classification["memory_action_policy"] == "ROUTE_TO_REPAIR_THEN_RETEST",
        "allowed_when_conditions_change": True,
        "confidence_decay_policy": "DECAY_TO_WATCH_AFTER_NEW_EVIDENCE",
        "memory_decay_policy": "FAST_DECAY_FRAGILE_OR_SPARSE_EVIDENCE" if "WATCH" in memory_classification else "MEDIUM_DECAY_CONDITION_SCOPED_NEGATIVE",
        "memory_override_policy": "NEW_REPAIR_OR_REGIME_VERSION_CAN_OVERRIDE_FOR_REPLAY_PAPER_ONLY",
        "owner_review_request_allowed": True,
        "validation_status": "PASS",
    }
