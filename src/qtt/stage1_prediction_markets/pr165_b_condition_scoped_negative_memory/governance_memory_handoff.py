"""Governance handoff rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_governance_memory_handoff_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "governance_memory_ref": ordinal_ref("PR165_B_GOVERNANCE_MEMORY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "governance_consumer": "governance_agent",
        "governance_review_required": classification["memory_action_policy"] in {"GOVERNANCE_REVIEW_REQUIRED", "MODEL_RISK_REVIEW_REQUIRED"},
        "commander_summary_route": "commander_agent",
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "validation_status": "PASS",
    }
