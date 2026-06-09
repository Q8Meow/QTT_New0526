"""Lineage graph rows for PR165-B memory records."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_lineage_graph_record(index: int, ctx: dict[str, Any], refs: dict[str, str], classification: dict[str, Any], route_agents: list[str]) -> dict[str, Any]:
    score = ctx["score"]
    candidate_id = score["candidate_packet_id"]
    edges = [
        ["QKU", score["qku_id"]],
        [score["qku_id"], "CandidatePacketV1"],
        ["CandidatePacketV1", candidate_id],
        [candidate_id, score["deterministic_score_component_record"]],
        [score["deterministic_score_component_record"], refs["condition_fingerprint_id"]],
        [refs["condition_fingerprint_id"], refs["combination_fingerprint_id"]],
        [refs["combination_fingerprint_id"], refs["asof_leakage_audit_ref"]],
        [refs["asof_leakage_audit_ref"], refs["evidence_sufficiency_ref"]],
        [refs["evidence_sufficiency_ref"], refs["scenario_outcome_ref"]],
        [refs["scenario_outcome_ref"], refs["outcome_attribution_ref"]],
        [refs["outcome_attribution_ref"], classification["memory_classification"]],
        [classification["memory_classification"], classification["memory_action_policy"]],
        [classification["memory_action_policy"], refs["agent_selection_overlay_ref"]],
        [refs["agent_selection_overlay_ref"], "responsible agents"],
        ["responsible agents", ",".join(route_agents)],
        [",".join(route_agents), "repair/retest route when applicable"],
        ["repair/retest route when applicable", "future PR consumers"],
        ["future PR consumers", "dashboard/governance/commander consumers"],
    ]
    return {
        "lineage_graph_ref": ordinal_ref("PR165_B_LINEAGE", index),
        "candidate_packet_id": candidate_id,
        "qku_id": score["qku_id"],
        "condition_fingerprint_id": refs["condition_fingerprint_id"],
        "combination_fingerprint_id": refs["combination_fingerprint_id"],
        "lineage_edges": edges,
        "upstream_pr_refs": score.get("upstream_pr_refs", []),
        "upstream_report_refs": score.get("upstream_report_refs", []),
        "downstream_agent_route": route_agents,
        "downstream_pr_route": ["PR165-C_OR_LATER", "PR167", "runtime/cache/dashboard"],
        "dashboard_consumer": "dashboard_future_consumer",
        "governance_consumer": "governance_agent",
        "authority_boundary": "REPLAY_PAPER_MEMORY_ONLY",
        "validation_status": "PASS",
    }
