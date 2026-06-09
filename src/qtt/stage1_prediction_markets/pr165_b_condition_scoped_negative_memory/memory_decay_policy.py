"""Memory decay and override rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def decay_class_for(classification: str) -> str:
    if classification == "STRUCTURAL_INVALIDITY_ARCHIVE_CANDIDATE":
        return "NO_DECAY_STRUCTURAL_INVALIDITY_ONLY"
    if classification in {"FRAGILE_HIGH_VARIANCE", "SPARSE_REGIME_WATCH", "FALSE_DISCOVERY_RISK_WATCH", "NEUTRAL_INSUFFICIENT_EVIDENCE"}:
        return "FAST_DECAY_FRAGILE_OR_SPARSE_EVIDENCE"
    if classification.startswith("NEGATIVE") or classification.endswith("DOMINATED") or classification.endswith("WEAK"):
        return "MEDIUM_DECAY_CONDITION_SCOPED_NEGATIVE"
    return "IMMEDIATE_REVIEW_AFTER_REPAIR"


def build_memory_decay_policy_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "memory_decay_policy_ref": ordinal_ref("PR165_B_MEMORY_DECAY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "memory_decay_class": decay_class_for(classification["memory_classification"]),
        "memory_decay_trigger": "NEW_EVIDENCE",
        "memory_decay_review_interval": "AFTER_EACH_REPLAY_PAPER_RETEST_OR_REGIME_CHANGE",
        "new_evidence_override_allowed": True,
        "repair_version_override_allowed": True,
        "regime_change_override_allowed": True,
        "formula_version_override_allowed": True,
        "parameter_stack_version_override_allowed": True,
        "source_provenance_upgrade_override_allowed": True,
        "quantum_formulation_repair_override_allowed": True,
        "validation_status": "PASS",
    }
