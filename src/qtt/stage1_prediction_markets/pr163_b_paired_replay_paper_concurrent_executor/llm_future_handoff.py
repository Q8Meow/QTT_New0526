"""Future LLM review handoff with no runtime LLM authority."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


def build_llm_handoff(index: int, ctx: dict[str, Any], divergence: dict[str, Any], remediation: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "llm_handoff_ref": plain_ref("LLM_HANDOFF", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "replay_trace_ref": ctx["replay_trace"]["replay_trace_ref"],
        "paper_trace_ref": ctx["paper_trace"]["paper_trace_ref"],
        "comparison_ref": comparison["comparison_ref"],
        "divergence_refs": [divergence["divergence_ref"]],
        "remediation_ref": remediation["remediation_ref"],
        "downstream_pr166_llm_slot_registry_ref": plain_ref("PR166_LLM_SLOT", index),
        "downstream_pr166_b_llm_source_candidate_extraction_ref": plain_ref("PR166B_SOURCE_EXTRACTION", index),
        "downstream_pr166_c_llm_replay_paper_impact_review_ref": plain_ref("PR166C_IMPACT_REVIEW", index),
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }
