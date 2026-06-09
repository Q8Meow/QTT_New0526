"""Replay/paper-only agent selection overlay rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref
from .negative_memory_action_policy import requires_repair, requires_retest


def overlay_action_for(classification: dict[str, Any]) -> str:
    memory_classification = classification["memory_classification"]
    action_policy = classification["memory_action_policy"]
    if memory_classification == "POSITIVE_CONDITION_SCOPED_PREFERRED":
        return "PREFER_IN_REPLAY_PAPER_QUEUE"
    if memory_classification.startswith("POSITIVE") or "WATCH" in memory_classification:
        return "WATCH_IN_REPLAY_PAPER_QUEUE"
    if requires_repair(action_policy):
        return "ROUTE_TO_REPAIR_QUEUE"
    if requires_retest(action_policy):
        return "ROUTE_TO_RETEST_QUEUE"
    if action_policy == "AVOID_ONLY_WITHIN_MATCHING_CONDITION":
        return "EXCLUDE_ONLY_UNDER_EXACT_MATCHING_REPLAY_PAPER_CONDITION"
    if action_policy in {"CONDITION_SCOPED_COOLDOWN", "DEMOTE_WITHIN_MATCHING_CONDITION"}:
        return "DEMOTE_IN_REPLAY_PAPER_QUEUE"
    return "NO_MEMORY_ADJUSTMENT"


def build_agent_selection_overlay_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_selection_overlay_ref": ordinal_ref("PR165_B_AGENT_SELECTION_OVERLAY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "overlay_action": overlay_action_for(classification),
        "replay_paper_only": True,
        "live_execution_allowed": False,
        "source_truth_accepted": False,
        "connector_bound": False,
        "private_state_used": False,
        "profit_evidence_created": False,
        "global_ban_without_structural_invalidity": False,
        "validation_status": "PASS",
    }
