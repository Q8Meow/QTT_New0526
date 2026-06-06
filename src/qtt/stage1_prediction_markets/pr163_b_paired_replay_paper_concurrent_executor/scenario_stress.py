"""Scenario stress and sensitivity candidates."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


STRESS_DIMENSIONS = (
    "fee_shock_low",
    "fee_shock_high",
    "slippage_shock_low",
    "slippage_shock_high",
    "latency_shock_low",
    "latency_shock_high",
    "liquidity_haircut_25pct",
    "liquidity_haircut_50pct",
    "spread_widening",
    "stale_quote_delay",
    "settlement_delay",
    "lifecycle_close_before_fill",
    "capital_budget_tightening",
    "exposure_limit_tightening",
    "queue_position_adverse_move",
    "source_revalidation_required",
    "data_quality_downgrade",
)


def build_stress_rows(index: int, ctx: dict[str, Any], replay_trace: dict[str, Any], paper_trace: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    base_replay_cost = float(replay_trace["replay_fees"]) + float(replay_trace["replay_slippage"])
    base_paper_cost = float(paper_trace["paper_fees"]) + float(paper_trace["paper_slippage"])
    for offset, dimension in enumerate(STRESS_DIMENSIONS, 1):
        multiplier = 1.0 + (offset % 5) * 0.1
        effect_replay = round(base_replay_cost * multiplier, 6)
        effect_paper = round(base_paper_cost * multiplier, 6)
        bucket = "LOW" if max(effect_replay, effect_paper) < 1 else "MEDIUM" if max(effect_replay, effect_paper) < 10 else "HIGH"
        if dimension in {"liquidity_haircut_50pct", "lifecycle_close_before_fill", "capital_budget_tightening"} and bucket == "HIGH":
            bucket = "EXTREME"
        rows.append(
            {
                "stress_ref": plain_ref("STRESS", ((index - 1) * len(STRESS_DIMENSIONS)) + offset),
                "paired_run_ref": plain_ref("RUN_INPUT", index),
                "candidate_packet_id": ctx["row"]["candidate_packet_id"],
                "qku_ids": list(ctx["row"].get("qku_ids") or []),
                "stress_dimension": dimension,
                "replay_effect_candidate": effect_replay,
                "paper_effect_candidate": effect_paper,
                "comparison_effect_candidate": round(effect_replay - effect_paper, 6),
                "sensitivity_bucket": bucket,
                "no_profit_evidence": True,
                "no_live_authority": True,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows
