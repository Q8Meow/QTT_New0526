"""PR164/PR165/PR166 and plugin handoff rows."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


def build_pr164_handoff(index: int, ctx: dict[str, Any], divergence: dict[str, Any], remediation: dict[str, Any], tca: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr164_handoff_ref": plain_ref("PR164_HANDOFF", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "review_evidence_refs": [
            ctx["replay_trace"]["replay_trace_ref"],
            ctx["paper_trace"]["paper_trace_ref"],
            ctx["comparison"]["comparison_ref"],
            divergence["divergence_ref"],
            remediation["remediation_ref"],
            tca["tca_ref"],
        ],
        "source_candidate_refs": list(ctx["row"].get("source_candidate_refs") or []),
        "leakage_guard_ref": ctx["leakage_guard"]["leakage_guard_ref"],
        "fill_integrity_ref": ctx["fill_integrity"]["fill_integrity_ref"],
        "review_required": True,
        "source_acceptance_created": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def build_pr165_handoff(index: int, ctx: dict[str, Any], tca: dict[str, Any], quantum_carry: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr165_handoff_ref": plain_ref("PR165_HANDOFF", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "scoring_input_refs": [
            ctx["comparison"]["comparison_ref"],
            tca["tca_ref"],
            ctx["walk_forward"]["walk_forward_ref"],
            quantum_carry["quantum_carry_ref"],
        ],
        "edge_after_cost_replay": ctx["comparison"]["edge_after_cost_replay"],
        "edge_after_cost_paper": ctx["comparison"]["edge_after_cost_paper"],
        "fill_qty_delta": ctx["comparison"]["fill_qty_delta"],
        "repairability": ctx["remediation"]["repairability"],
        "no_score_created": True,
        "no_rank_created": True,
        "no_promotion_created": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def build_pr166_handoff(index: int, ctx: dict[str, Any], llm_handoff: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr166_handoff_ref": plain_ref("PR166_HANDOFF", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "llm_future_review_handoff_ref": llm_handoff["llm_handoff_ref"],
        "review_research_only": True,
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }


def build_pr162e_update(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugin_replay_paper_compatibility_ref": plain_ref("PR162E_COMPAT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "formula_refs": [ctx["row"].get("callable_ref")] if ctx["row"].get("callable_ref") else [],
        "plugin_intake_recommendation": "CANDIDATE_ONLY_NONLIVE_REVIEW_AFTER_PR164_PR165",
        "live_connector_activation": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
