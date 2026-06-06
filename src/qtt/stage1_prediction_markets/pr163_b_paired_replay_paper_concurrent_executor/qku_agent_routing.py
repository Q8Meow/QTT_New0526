"""QKU/formula/algorithm/agent routing for PR163-B."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


DOWNSTREAM_AGENTS = (
    "Replay Lane Executor",
    "Paper Lane Executor",
    "Paired Comparison Engine",
    "Divergence Classifier",
    "Transaction Cost Analysis Engine",
    "Rejection Remediation Classifier",
    "QKU Compute Engine",
    "Formula/Algorithm Runtime candidate lane",
    "Feature Builder",
    "Parameter Stack Agent",
    "Risk Manager",
    "Capital Allocation",
    "Quantum Advisory / Quantum Mapping Agent",
    "PR164 Review/Provenance",
    "PR165 Scoring/Ranking",
    "PR166 LLM Review/Research lane",
    "PR162E Plugin Intake",
)


def build_qku_route(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    row = ctx["row"]
    return {
        "qku_agent_routing_ref": plain_ref("QKU_AGENT_ROUTE", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "formulation_refs": [row.get("formulation_ref")] if row.get("formulation_ref") else [],
        "formula_refs": [row.get("callable_ref")] if row.get("callable_ref") else [],
        "algorithm_refs": [ctx["candidate"].get("algorithm_family", "PR163B_PAIRED_EXECUTOR")],
        "upstream_refs": list(row.get("upstream_refs") or []),
        "downstream_refs": list(DOWNSTREAM_AGENTS),
        "replay_trace_ref": ctx["replay_trace"]["replay_trace_ref"],
        "paper_trace_ref": ctx["paper_trace"]["paper_trace_ref"],
        "comparison_ref": ctx["comparison"]["comparison_ref"],
        "tca_ref": ctx["tca"]["tca_ref"],
        "qku_prioritization_update_ref": plain_ref("QKU_PRIORITY_UPDATE", index),
        "orphan_flag": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
