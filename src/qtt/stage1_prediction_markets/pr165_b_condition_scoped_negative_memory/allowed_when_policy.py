"""Allowed-when condition policy rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_allowed_when_policy_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_when_policy_ref": ordinal_ref("PR165_B_ALLOWED_WHEN", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "allowed_condition_scope_ref": f"{condition_id}::ALLOWED_WHEN_CONDITIONS_CHANGE_OR_POLICY_PASS",
        "avoid_condition_scope_ref": f"{condition_id}::AVOID_ONLY_WITHIN_MATCHING_CONDITION_IF_POLICY_REQUIRES",
        "allowed_when_conditions_change": True,
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "validation_status": "PASS",
    }
