"""PaperDecisionIntentV1 construction."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


def model_edge_for_index(index: int) -> float:
    return round(0.055 + ((index % 7) * 0.002), 6)


def build_decision_intent(
    *,
    index: int,
    candidate: dict[str, Any],
    row_resolution: dict[str, Any],
    scenario: Any,
    price_candidate: float,
    robust_edge_after_cost: float,
) -> dict[str, Any]:
    decision_ref = plain_ref("DECISION_INTENT", index)
    order_ref = plain_ref("ORDER_INTENT", index)
    return {
        "decision_intent_ref": decision_ref,
        "candidate_packet_id": candidate["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids") or candidate.get("qku_ids", []),
        "formulation_refs": [ref for ref in [row_resolution.get("formulation_ref") or candidate.get("formulation_ref")] if ref],
        "algorithm_refs": [candidate.get("algorithm_family") or "PR163_SYNTHETIC_PAPER_DECISION_ALGORITHM"],
        "model_signal_refs": [plain_ref("MODEL_SIGNAL", index)],
        "paper_binding_refs": row_resolution.get("paper_binding_refs", []),
        "source_candidate_refs": row_resolution.get("source_candidate_refs", []),
        "decision_action": "PAPER_PLACE_ORDER_CANDIDATE",
        "side_candidate": scenario.side,
        "order_type_candidate": scenario.order_type,
        "price_candidate": price_candidate,
        "size_candidate": scenario.requested_qty,
        "time_in_force_candidate": scenario.time_in_force,
        "robust_edge_after_cost_candidate": robust_edge_after_cost,
        "reason_codes": [f"PR163_{scenario.name}_DETERMINISTIC_PAPER_DECISION"],
        "downstream_order_intent_ref": order_ref,
        "downstream_pretrade_receipt_ref": plain_ref("PRETRADE_RECEIPT", index),
        "downstream_pr163_b_paired_replay_paper_executor_ref": plain_ref("PR163B_HANDOFF", index),
        "downstream_pr164_review_provenance_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_scoring_ranking_ref": plain_ref("PR165_HANDOFF", index),
        "downstream_pr166_llm_review_lane_ref": plain_ref("PR166_HANDOFF", index),
        "no_order_ready_claim": True,
        "no_live_order_authority": True,
        "no_profit_evidence": True,
        "llm_hot_path_allowed": False,
        "llm_live_order_release_allowed": False,
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }
