"""Agent route rows for PR165-B memory records."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref
from .negative_memory_action_policy import requires_repair
from .quantum_negative_memory import is_quantum_compatible


BASE_ROUTES = (
    "negative_memory_agent",
    "risk_agent",
    "replay_agent",
    "paper_agent",
    "dashboard_future_consumer",
    "governance_agent",
    "commander_agent",
)


def downstream_agents(ctx: dict[str, Any], classification: dict[str, Any]) -> list[str]:
    agents = list(BASE_ROUTES)
    reason = set(classification["reason_codes"])
    if "PR165_B_COST_DEGRADATION" in reason or "PR165_B_ADVERSE_SELECTION_DEGRADATION" in reason:
        agents.append("tca_agent")
    if "PR165_B_LATENCY_DEGRADATION" in reason:
        agents.append("latency_agent")
    if "PR165_B_LIQUIDITY_DEGRADATION" in reason:
        agents.append("liquidity_agent")
    if "PR165_B_MODEL_RISK_DEGRADATION" in reason:
        agents.append("model_risk_agent")
    if is_quantum_compatible(ctx):
        agents.append("quantum_mapper_advisory_agent")
    if requires_repair(classification["memory_action_policy"]):
        agents.append("repair_agent")
    return sorted(dict.fromkeys(agents))


def build_agent_memory_route_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_memory_route_ref": ordinal_ref("PR165_B_AGENT_MEMORY_ROUTE", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "downstream_agent_route": downstream_agents(ctx, classification),
        "downstream_pr_route": list(ctx["score"].get("upstream_pr_refs", [])) + ["PR165-B", "PR165-C_OR_LATER"],
        "dashboard_consumer": "dashboard_future_consumer",
        "governance_consumer": "governance_agent",
        "lineage_graph_ref": ctx["score"]["lineage_graph_ref"],
        "authority_boundary": "REPLAY_PAPER_MEMORY_ONLY",
        "validation_status": "PASS",
    }
