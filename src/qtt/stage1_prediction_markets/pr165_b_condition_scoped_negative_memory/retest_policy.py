"""Retest policy and queue rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def trigger_for(action_policy: str, classification: str) -> str:
    if action_policy == "FALSE_DISCOVERY_RETEST_REQUIRED":
        return "FALSE_DISCOVERY_RETEST_REQUIRED"
    if action_policy == "SPARSE_REGIME_EVIDENCE_COLLECTION_REQUIRED":
        return "SPARSE_REGIME_EVIDENCE_COLLECTION_REQUIRED"
    if action_policy == "QUANTUM_FORMULATION_REPAIR_REQUIRED":
        return "QUANTUM_FORMULATION_REPAIRED"
    if action_policy == "MODEL_RISK_REVIEW_REQUIRED":
        return "MODEL_RISK_REVIEW_COMPLETED"
    if action_policy == "TCA_REPAIR_REQUIRED":
        return "TCA_COMPONENT_REPAIRED"
    if action_policy == "LATENCY_REPAIR_REQUIRED":
        return "LATENCY_BUCKET_IMPROVED"
    if action_policy == "LIQUIDITY_REPAIR_REQUIRED":
        return "LIQUIDITY_BUCKET_IMPROVED"
    if action_policy == "SOURCE_RESEARCH_REPAIR_REQUIRED":
        return "SOURCE_PROVENANCE_IMPROVED"
    if classification == "NEGATIVE_CONDITION_SCOPED_COOLDOWN":
        return "NEGATIVE_MEMORY_DECAY_EXPIRED"
    return "NEW_PAPER_EVIDENCE"


def build_retest_policy_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    trigger = trigger_for(classification["memory_action_policy"], classification["memory_classification"])
    return {
        "retest_policy_ref": ordinal_ref("PR165_B_RETEST_POLICY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "retest_required": True,
        "retest_condition": "SAME_CONDITION_SCOPE_OR_RECORDED_CONDITION_CHANGE",
        "retest_trigger": trigger,
        "minimum_new_evidence": 12 if "SPARSE" not in classification["memory_classification"] else 24,
        "retest_metric": "FALSE_DISCOVERY_ADJUSTED_RISK_ADJUSTED_NET_EDGE_AND_REPLAY_PAPER_ALIGNMENT",
        "expected_repair_or_regime_change": trigger,
        "pass_condition": "ADJUSTED_CONFIDENCE_AND_NET_EDGE_CLEAR_CONDITION_SCOPE_POLICY",
        "fail_condition": "PERSISTENT_DOMINANT_DEGRADATION_UNDER_MATCHING_CONDITION",
        "route_after_pass": "ALLOW_CONDITION_SCOPED_SELECTION",
        "route_after_fail": "DEMOTE_WITHIN_MATCHING_CONDITION",
        "owner_dashboard_visibility": True,
        "authority_boundary": "REPLAY_PAPER_MEMORY_ONLY",
        "validation_status": "PASS",
    }


def build_retest_queue_record(index: int, retest_policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "retest_queue_id": ordinal_ref("PR165_B_RETEST_QUEUE", index),
        "candidate_packet_id": retest_policy["candidate_packet_id"],
        "candidate_version": f"{retest_policy['candidate_packet_id']}::VERSION::PR165_B_MEMORY",
        "condition_fingerprint_id": retest_policy["condition_fingerprint_id"],
        "combination_fingerprint_id": retest_policy["combination_fingerprint_id"],
        "memory_classification": retest_policy["memory_classification"],
        "memory_action_policy": retest_policy["memory_action_policy"],
        "retest_trigger": retest_policy["retest_trigger"],
        "minimum_new_evidence": retest_policy["minimum_new_evidence"],
        "retest_metric": retest_policy["retest_metric"],
        "expected_repair_or_regime_change": retest_policy["expected_repair_or_regime_change"],
        "pass_condition": retest_policy["pass_condition"],
        "fail_condition": retest_policy["fail_condition"],
        "route_after_pass": retest_policy["route_after_pass"],
        "route_after_fail": retest_policy["route_after_fail"],
        "owner_dashboard_visibility": retest_policy["owner_dashboard_visibility"],
        "authority_boundary": retest_policy["authority_boundary"],
        "validation_status": "PASS",
    }
