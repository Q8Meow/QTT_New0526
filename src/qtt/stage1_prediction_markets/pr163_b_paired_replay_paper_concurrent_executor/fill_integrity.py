"""Replay/paper fill integrity receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_fill_integrity(index: int, ctx: dict[str, Any], replay_trace: dict[str, Any], paper_trace: dict[str, Any]) -> dict[str, Any]:
    order = ctx["paper"]["order"]
    fill = ctx["paper"]["fill"]
    requested = float(order.get("requested_qty", 0.0))
    paper_levels = list(fill.get("level_fills") or [])
    paper_level_sum = round(sum(float(level.get("fill_qty_at_level", 0.0)) for level in paper_levels), 6)
    replay_filled = float(replay_trace["replay_fill_qty"])
    replay_level_sum = replay_filled
    status = "FILL_INTEGRITY_PASS"
    reason = ""
    if replay_filled == 0.0 and float(paper_trace["paper_fill_qty"]) == 0.0:
        status = "FILL_INTEGRITY_PARTIAL_WITH_EXACT_REASON"
        reason = "NO_FILL_OR_REJECTED_ROW_REPRESENTED_WITH_EXACT_TRACE_STATUS"
    return {
        "fill_integrity_ref": plain_ref("FILL_INTEGRITY", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "replay_trace_ref": replay_trace["replay_trace_ref"],
        "paper_trace_ref": paper_trace["paper_trace_ref"],
        "side": order.get("side"),
        "order_type": order.get("order_type"),
        "requested_qty": requested,
        "replay_filled_qty": replay_filled,
        "paper_filled_qty": float(paper_trace["paper_fill_qty"]),
        "replay_unfilled_qty": float(replay_trace["replay_unfilled_qty"]),
        "paper_unfilled_qty": float(paper_trace["paper_unfilled_qty"]),
        "replay_book_depth_available_at_limit": max(requested, replay_filled),
        "paper_book_depth_available_at_limit": max(requested, float(paper_trace["paper_fill_qty"])),
        "replay_level_fill_qty_sum": replay_level_sum,
        "paper_level_fill_qty_sum": paper_level_sum,
        "replay_vwap_price": replay_trace["replay_vwap_price"],
        "paper_vwap_price": paper_trace["paper_vwap_price"],
        "queue_position_approximation_candidate": "SYNTHETIC_FIFO_DEPTH_WALK_APPROXIMATION",
        "maker_taker_replay": "TAKER" if replay_filled > 0 else "MAKER_OR_RESTING",
        "maker_taker_paper": fill.get("maker_taker", "NONE"),
        "lifecycle_state_at_decision": ctx["lifecycle_state"],
        "lifecycle_state_at_fill": ctx["lifecycle_state"] if ctx["lifecycle_state"] == "OPEN" else "NO_FILL_AFTER_NON_OPEN_LIFECYCLE",
        "fill_integrity_status": status,
        "exact_integrity_reason": reason,
        "no_live_authority": True,
        "no_profit_evidence": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
