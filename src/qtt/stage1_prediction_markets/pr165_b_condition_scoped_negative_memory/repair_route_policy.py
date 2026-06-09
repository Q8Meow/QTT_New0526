"""Repair route handoff rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref
from .negative_memory_action_policy import requires_repair


def repair_agent_for(action_policy: str) -> str:
    return {
        "TCA_REPAIR_REQUIRED": "tca_repair_agent",
        "LATENCY_REPAIR_REQUIRED": "latency_repair_agent",
        "LIQUIDITY_REPAIR_REQUIRED": "liquidity_repair_agent",
        "MODEL_RISK_REVIEW_REQUIRED": "model_risk_agent",
        "SOURCE_RESEARCH_REPAIR_REQUIRED": "acquisition_repair_agent",
        "QUANTUM_FORMULATION_REPAIR_REQUIRED": "quantum_mapper_advisory_agent",
        "ROUTE_TO_REPAIR_THEN_RETEST": "negative_memory_agent",
    }.get(action_policy, "replay_paper_agent")


def build_repair_route_record(index: int, ctx: dict[str, Any], condition_id: str, classification: dict[str, Any]) -> dict[str, Any] | None:
    action = classification["memory_action_policy"]
    if not requires_repair(action):
        return None
    candidate_id = ctx["score"]["candidate_packet_id"]
    agent = repair_agent_for(action)
    return {
        "repair_route_ref": ordinal_ref("PR165_B_REPAIR_ROUTE", index),
        "candidate_packet_id": candidate_id,
        "candidate_version": f"{candidate_id}::VERSION::PR165_B_MEMORY_REPAIR_PLAN",
        "repair_event_id": ordinal_ref("PR165_B_REPAIR_EVENT", index),
        "parent_candidate_version": f"{candidate_id}::VERSION::PR165",
        "repair_reason_codes": classification["reason_codes"],
        "responsible_repair_agent": agent,
        "missing_or_weak_fields": classification["reason_codes"],
        "required_materialization_action": action,
        "upstream_evidence_refs": ctx["score"].get("upstream_report_refs", []),
        "downstream_retest_route": "PR165_B_REPLAY_PAPER_RETEST_QUEUE",
        "replay_paper_retest_required": True,
        "promotion_condition": "RETEST_PASSES_WITH_CONDITION_SCOPE_AND_FDR_GUARDRAILS",
        "demotion_condition": "RETEST_CONFIRMS_DOMINANT_DEGRADATION",
        "archive_condition": "STRUCTURAL_INVALIDITY_ONLY_WITH_COMPLETE_EVIDENCE",
        "condition_scope": condition_id,
        "authority_boundary": "REPLAY_PAPER_MEMORY_ONLY",
        "target_pr_or_workflow": "PR165-C_OR_LATER_REPAIR_WORKFLOW",
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "validation_status": "PASS",
    }
