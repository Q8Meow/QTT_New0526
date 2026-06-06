"""Transaction cost analysis candidate rows."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_tca(index: int, ctx: dict[str, Any], replay_trace: dict[str, Any], paper_trace: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    arrival = float(ctx["paper"]["latency"].get("arrival_mid", 0.0))
    replay_vwap = float(replay_trace["replay_vwap_price"])
    paper_vwap = float(paper_trace["paper_vwap_price"])
    return {
        "tca_ref": plain_ref("TCA", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "venue_scope": ctx["paper"]["order"].get("venue_scope"),
        "market_scope": ctx["paper"]["order"].get("market_scope"),
        "arrival_mid": arrival,
        "replay_vwap": replay_vwap,
        "paper_vwap": paper_vwap,
        "replay_fees": replay_trace["replay_fees"],
        "paper_fees": paper_trace["paper_fees"],
        "replay_slippage": replay_trace["replay_slippage"],
        "paper_slippage": paper_trace["paper_slippage"],
        "replay_spread_cost": replay_trace["replay_spread_cost"],
        "paper_spread_cost": paper_trace["paper_spread_cost"],
        "replay_latency_cost_candidate": replay_trace["replay_latency_cost_candidate"],
        "paper_latency_cost_candidate": paper_trace["paper_latency_cost_candidate"],
        "replay_liquidity_impact_candidate": round(abs(replay_vwap - arrival) * float(replay_trace["replay_fill_qty"]), 6),
        "paper_liquidity_impact_candidate": round(abs(paper_vwap - arrival) * float(paper_trace["paper_fill_qty"]), 6),
        "replay_implementation_shortfall_candidate": round(float(replay_trace["replay_slippage"]) + float(replay_trace["replay_fees"]) + float(replay_trace["replay_spread_cost"]), 6),
        "paper_implementation_shortfall_candidate": round(float(paper_trace["paper_slippage"]) + float(paper_trace["paper_fees"]) + float(paper_trace["paper_spread_cost"]), 6),
        "edge_before_cost": ctx["edge_before_cost"],
        "edge_after_cost_replay": comparison["edge_after_cost_replay"],
        "edge_after_cost_paper": comparison["edge_after_cost_paper"],
        "cost_model_truth_status": "SYNTHETIC_FIXTURE_COST_MODEL",
        "tca_status": "TCA_COMPLETE",
        "no_profit_evidence": True,
        "no_live_authority": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
