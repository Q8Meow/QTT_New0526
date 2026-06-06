"""Non-live execution outcome candidate receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_outcome(index: int, lane: str, ctx: dict[str, Any], trace_refs: list[str], comparison_refs: list[str]) -> dict[str, Any]:
    lane_offset = {"REPLAY": 0, "PAPER": 1, "PAIRED": 2}[lane]
    return {
        "outcome_candidate_ref": plain_ref("OUTCOME_CANDIDATE", ((index - 1) * 3) + lane_offset + 1),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "lane": lane,
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "trace_refs": trace_refs,
        "comparison_refs": comparison_refs,
        "accounting_candidate_fields": {
            "replay_accounting_delta_candidate": ctx["replay_trace"]["replay_accounting_delta_candidate"],
            "paper_accounting_delta_candidate": ctx["paper_trace"]["paper_accounting_delta_candidate"],
        },
        "settlement_candidate_fields_if_available": {
            "settlement_label_ref": ctx["settlement_label_ref"],
            "settlement_used_for_pretrade": False,
        },
        "truth_status": "NONLIVE_SYNTHETIC_OUTCOME_CANDIDATE",
        "review_required_by_pr164": True,
        "scoring_required_by_pr165": True,
        "owner_promotion_review_required": True,
        "final_result_packet_created": False,
        "profit_evidence_created": False,
        "live_authority_created": False,
        "order_ready_claim_created": False,
        "source_accepted": False,
        "connector_bound": False,
        "private_state_fetched": False,
        "runtime_cash_receipt_created": False,
        "quantum_advantage_claimed": False,
        "llm_result_rewrite_used": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
