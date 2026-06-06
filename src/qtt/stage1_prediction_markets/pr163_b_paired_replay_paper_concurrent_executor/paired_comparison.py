"""Paired replay/paper comparison candidates."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_comparison(index: int, ctx: dict[str, Any], replay_trace: dict[str, Any], paper_trace: dict[str, Any], fill_integrity: dict[str, Any]) -> dict[str, Any]:
    replay_edge = round(float(ctx["edge_before_cost"]) - float(replay_trace["replay_fees"]) - float(replay_trace["replay_slippage"]) - float(replay_trace["replay_spread_cost"]), 6)
    paper_edge = round(float(ctx["edge_before_cost"]) - float(paper_trace["paper_fees"]) - float(paper_trace["paper_slippage"]) - float(paper_trace["paper_spread_cost"]), 6)
    return {
        "comparison_ref": plain_ref("COMPARISON", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "replay_trace_ref": replay_trace["replay_trace_ref"],
        "paper_trace_ref": paper_trace["paper_trace_ref"],
        "fill_integrity_ref": fill_integrity["fill_integrity_ref"],
        "decision_match": replay_trace["replay_decision_candidate"].startswith("REPLAY_EXECUTE") == paper_trace["paper_decision_candidate"].startswith("PAPER_PLACE"),
        "pretrade_status_match": replay_trace["replay_pretrade_status"].endswith("PASS") == paper_trace["paper_pretrade_status"].endswith("PASS"),
        "fill_status_match": replay_trace["replay_fill_status"].replace("REPLAY_", "") == paper_trace["paper_fill_status"].replace("PAPER_", ""),
        "fill_qty_delta": round(float(replay_trace["replay_fill_qty"]) - float(paper_trace["paper_fill_qty"]), 6),
        "fill_price_delta": round(float(replay_trace["replay_vwap_price"]) - float(paper_trace["paper_vwap_price"]), 6),
        "fee_delta": round(float(replay_trace["replay_fees"]) - float(paper_trace["paper_fees"]), 6),
        "slippage_delta": round(float(replay_trace["replay_slippage"]) - float(paper_trace["paper_slippage"]), 6),
        "spread_cost_delta": round(float(replay_trace["replay_spread_cost"]) - float(paper_trace["paper_spread_cost"]), 6),
        "latency_delta": round(float(replay_trace["replay_latency_cost_candidate"]) - float(paper_trace["paper_latency_cost_candidate"]), 6),
        "cost_adjusted_price_delta": round(float(replay_trace["replay_cost_adjusted_price"]) - float(paper_trace["paper_cost_adjusted_price"]), 6),
        "cash_delta_difference": round(float(replay_trace["replay_cash_delta_candidate"]) - float(paper_trace["paper_cash_delta_candidate"]), 6),
        "position_delta_difference": round(float(replay_trace["replay_position_delta"]) - float(paper_trace["paper_position_delta"]), 6),
        "accounting_delta_difference_candidate": round(float(replay_trace["replay_accounting_delta_candidate"]) - float(paper_trace["paper_accounting_delta_candidate"]), 6),
        "edge_after_cost_replay": replay_edge,
        "edge_after_cost_paper": paper_edge,
        "settlement_status_if_available": "SETTLEMENT_LABEL_CANDIDATE_AVAILABLE_POST_RUN" if ctx["settlement_label_ref"] else "SETTLEMENT_LABEL_MISSING",
        "data_quality_tier": ctx["row"].get("data_quality_tier", "DQ0_SYNTHETIC_TEST_ONLY"),
        "comparison_status": "PAIRED_COMPARISON_COMPLETE",
        "no_profit_evidence": True,
        "no_live_authority": True,
        "no_rank_created": True,
        "no_promotion_created": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
