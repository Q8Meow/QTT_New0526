"""Condition fingerprint records for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import numeric_suffix, ordinal_ref


def _bucket(value: float, low: float, high: float, labels: tuple[str, str, str]) -> str:
    if value <= low:
        return labels[0]
    if value >= high:
        return labels[2]
    return labels[1]


def build_condition_fingerprint_record(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    handoff_scope = dict(ctx["handoff"].get("condition_scope") or {})
    tca = ctx["tca"]
    liquidity = ctx["liquidity"]
    model_risk = ctx["model_risk"]
    quantum = ctx["quantum"]
    seq = numeric_suffix(score["candidate_packet_id"])
    provenance_score = float(ctx["provenance"].get("provenance_quality_score", 65.0))
    repair_score = float(ctx["repair_confidence"].get("repair_confidence_score", 0.75))
    condition_payload = {
        "venue": handoff_scope.get("venue", "VENUE_NEUTRAL_SYNTHETIC_FIXTURE"),
        "market_type": "PREDICTION_MARKET_BINARY_OR_COMPLEMENT_CANDIDATE",
        "event_type": handoff_scope.get("event_type", "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE"),
        "market_id_or_candidate_market_ref": f"PR165_B_CANDIDATE_MARKET::{seq:06d}",
        "side": "YES" if seq % 2 == 0 else "NO",
        "order_type_candidate": "LIMIT_MAKER" if seq % 3 else "MARKETABLE_LIMIT",
        "entry_price_bucket": _bucket(float(tca.get("net_edge_candidate", 0.0)), -0.25, 0.05, ("LOW_EDGE_ENTRY", "MID_EDGE_ENTRY", "HIGH_EDGE_ENTRY")),
        "spread_bucket": handoff_scope.get("spread_bucket") or _bucket(float(tca.get("spread_cost", 0.0)), 0.08, 0.35, ("TIGHT", "MODERATE", "WIDE")),
        "liquidity_bucket": handoff_scope.get("liquidity_bucket") or _bucket(float(liquidity.get("liquidity_fill_probability_score", 75.0)), 72.0, 88.0, ("LOW", "MEDIUM", "HIGH")),
        "depth_bucket": _bucket(float(liquidity.get("order_size_to_depth_ratio", 0.5)), 0.20, 0.70, ("DEEP", "BALANCED", "THIN")),
        "latency_bucket": handoff_scope.get("latency_bucket", "MEDIUM"),
        "time_to_resolution_bucket": liquidity.get("time_to_resolution_bucket", "MEDIUM_TIME_TO_RESOLUTION"),
        "market_maturity_bucket": "NEAR_RESOLUTION" if seq % 7 == 0 else "MATURE_MARKET" if seq % 5 else "EARLY_MARKET",
        "volatility_bucket": "HIGH_VOLATILITY" if seq % 11 == 0 else "NORMAL_VOLATILITY",
        "fee_bucket": _bucket(float(tca.get("fee_cost", 0.0)), 0.012, 0.04, ("LOW_FEE", "MEDIUM_FEE", "HIGH_FEE")),
        "slippage_bucket": _bucket(float(tca.get("slippage_cost", 0.0)), 0.04, 0.18, ("LOW_SLIPPAGE", "MEDIUM_SLIPPAGE", "HIGH_SLIPPAGE")),
        "yes_no_complement_consistency_bucket": "CONSISTENT_COMPLEMENT" if seq % 37 else "COMPLEMENT_RETEST_REQUIRED",
        "source_provenance_tier": _bucket(provenance_score, 66.0, 76.0, ("LOW_PROVENANCE", "MEDIUM_PROVENANCE", "HIGH_PROVENANCE")),
        "model_risk_tier": model_risk.get("model_materiality_tier", "MEDIUM_REPLAY_PAPER_PRIORITY"),
        "repair_confidence_tier": _bucket(repair_score, 0.74, 0.82, ("LOW_REPAIR_CONFIDENCE", "MEDIUM_REPAIR_CONFIDENCE", "HIGH_REPAIR_CONFIDENCE")),
        "rank_confidence_tier": score.get("score_confidence_tier", "MEDIUM_CONFIDENCE_CANDIDATE_ESTIMATE_RANK"),
        "quantum_formulation_class": quantum.get("quantum_formulation_class", "CLASSICAL_ONLY"),
        "hot_path_lane": ctx["latency_lane"].get("hot_path_lane", "REPLAY_PAPER_ONLY"),
        "portfolio_cluster": ctx["portfolio"].get("portfolio_cluster_ref", f"PR165_PORTFOLIO_CLUSTER::{seq % 19:02d}"),
        "duplicate_edge_cluster": f"PR165_DUPLICATE_EDGE_CLUSTER::{seq % 23:02d}",
        "event_concentration_group": f"PR165_EVENT_CONCENTRATION_GROUP::{seq % 17:02d}",
        "formula_family": ctx["formula_family"],
        "algorithm_family": ctx["algorithm_family"],
        "parameter_stack_family": ctx["parameter_stack_family"],
    }
    return {
        "condition_fingerprint_id": ordinal_ref("PR165_B_CONDITION_FINGERPRINT", index),
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "condition_scope": condition_payload,
        **condition_payload,
        "deterministic_materialization_policy": "FIELD_ORDERED_REPLAY_PAPER_CANDIDATE_BUCKETS",
        "validation_status": "PASS",
    }
