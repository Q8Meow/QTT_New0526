"""Future LLM handoff/exclusion receipts without runtime LLM authority."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


ALLOWED_FUTURE_LLM_ROLES = (
    "source-candidate extraction",
    "event/news summarization into candidate features",
    "research-source mapping",
    "QKU explanation and provenance",
    "anomaly annotation",
    "post-run replay/paper review",
    "owner dashboard summaries",
    "strategy failure diagnosis",
    "feature-candidate scouting",
    "LLM-assisted formulation proposals requiring deterministic code verification",
)

DISALLOWED_LLM_ROLES = (
    "LLM decides live trade",
    "LLM releases order",
    "LLM changes score without deterministic receipt",
    "LLM rewrites replay/paper result",
    "LLM creates accepted source truth",
    "LLM runs in hot order path",
)


def build_llm_future_handoff(index: int, row_resolution: dict[str, Any], capture_bundle_ref: str) -> dict[str, Any]:
    return {
        "llm_future_handoff_exclusion_receipt_ref": plain_ref("LLM_FUTURE_HANDOFF", index),
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "formulation_refs": [row_resolution.get("formulation_ref")] if row_resolution.get("formulation_ref") else [],
        "paper_capture_bundle_refs": [capture_bundle_ref],
        "downstream_pr166_llm_slot_registry_ref": plain_ref("PR166_LLM_SLOT_REGISTRY_HANDOFF", index),
        "downstream_pr166_b_llm_source_candidate_extraction_ref": plain_ref("PR166B_LLM_SOURCE_EXTRACTION_HANDOFF", index),
        "downstream_pr166_c_llm_replay_paper_impact_review_ref": plain_ref("PR166C_LLM_IMPACT_REVIEW_HANDOFF", index),
        "allowed_future_llm_roles": list(ALLOWED_FUTURE_LLM_ROLES),
        "disallowed_llm_roles": list(DISALLOWED_LLM_ROLES),
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }
