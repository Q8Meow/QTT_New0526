#!/usr/bin/env python3
"""Regime-conditioned memory seed builder for PR168-RP."""

from __future__ import annotations

from typing import Any


def regime_seed_row(computed: dict[str, Any]) -> dict[str, Any]:
    metrics = computed["metrics"]
    micro = computed["microstructure"]
    return {
        "regime_memory_ref": f"PR168_RP_REGIME::{computed['result_ref']}",
        "canonical_row_key": computed["canonical_row_key"],
        "qku_id": computed["qku_id"],
        "venue_platform_bucket": micro.get("venue"),
        "market_family_bucket": computed.get("market_scope", "prediction_market_stage1_index"),
        "event_category_bucket": metrics.get("event_category_exposure"),
        "liquidity_bucket": micro.get("liquidity_bucket"),
        "spread_bucket": micro.get("spread_bucket"),
        "time_to_resolution_bucket": metrics.get("time_to_resolution_bucket"),
        "latency_bucket": micro.get("latency_bucket"),
        "volatility_probability_movement_bucket": "PROBABILITY_EDGE_BUCKET",
        "news_social_shock_bucket": "UNOBSERVED_REPLAY_PAPER_GAP",
        "order_size_bucket": "MIN_SIZE_CANDIDATE",
        "fill_regime_bucket": micro.get("fill_regime_bucket"),
        "capacity_bucket": micro.get("crowding_score"),
        "cost_bucket": "COST_DOMINATED" if computed["computed_status"] == "COMPUTED_NEGATIVE_EDGE" else "COST_PASS",
        "calibration_bucket": metrics.get("reliability_bin"),
        "order_policy_bucket": "NO_TRADE_DOMINANCE_TESTED",
        "no_trade_dominance_bucket": "NO_TRADE_DOMINATES" if metrics["no_trade_comparison_margin"] <= 0 else "ACTION_MARGIN_GAP",
        "negative_recovery_success_bucket": "NO_REPAIR_PROMOTION",
        "negative_recovery_failure_bucket": "MISSING_DEFAULT_OR_COST_DOMINATED",
        "producer": "PR168_RP_REGIME_MEMORY_SEED",
        "consumer": "PR168_RANK",
        "upstream_source": computed["result_ref"],
        "downstream_route": "PR168_RP_RegimeConditionedMemorySeed.report.json",
        "owning_agent": "Memory Agent",
        "no_orphan_status": "CONNECTED_TO_REGIME_MEMORY_CONSUMER",
    }
