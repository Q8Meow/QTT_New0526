"""Downstream handoff records for PR163-B, PR164, PR165, PR166, and PR162E."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


def build_downstream_handoff(index: int, target_pr: str, row_resolution: dict[str, Any], capture_bundle_ref: str) -> dict[str, Any]:
    normalized = target_pr.replace("-", "").replace("_", "")
    return {
        "downstream_handoff_ref": plain_ref(f"{normalized}_HANDOFF", index),
        "target_pr": target_pr,
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "paper_capture_bundle_ref": capture_bundle_ref,
        "handoff_status": "PR163_PAPER_CAPTURE_HANDOFF_READY_NON_RESULT",
        "replay_result_placeholder_ref_only": plain_ref("REPLAY_RESULT_PLACEHOLDER_ONLY", index),
        "paper_result_created": False,
        "replay_result_created": False,
        "score_created": False,
        "rank_created": False,
        "promotion_created": False,
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }


def build_pr162e_compatibility(index: int, row_resolution: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugin_paper_adapter_compatibility_ref": plain_ref("PR162E_PLUGIN_COMPAT", index),
        "target_pr": "PR162E",
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "plugin_intake_status": "PAPER_ADAPTER_CAPTURE_COMPATIBLE_NONLIVE",
        "live_connector_activation": False,
        "source_acceptance_created": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
