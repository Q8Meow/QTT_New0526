"""Latency, hot-path, and precompute routing for PR162R."""

from __future__ import annotations

from typing import Any


HOT_TIERS = {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA", "TIER_2_VECTORIZED_FEATURE_FORMULA"}
BATCH_TIERS = {"TIER_3_CLASSICAL_OPTIMIZER_FORMULA", "TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER"}


def build_latency_precompute_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        tier = str(packet.get("compute_tier"))
        is_quantum = packet.get("candidate_type") == "QUANTUM_FORMULATION"
        batch_only = tier in BATCH_TIERS or is_quantum
        benchmark_ref = f"PR162R_MISSING_BINDING_ACTION::{index + (2 * len(packets)):05d}"
        rows.append(
            {
                "latency_precompute_route_id": f"PR162R_LATENCY_PRECOMPUTE::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "formulation_ref": packet.get("formulation_ref"),
                "qku_id": _first_qku(packet),
                "latency_precompute_route": _route(tier, is_quantum),
                "compute_tier": tier,
                "latency_class": packet.get("latency_class"),
                "estimated_compute_cost_class": _cost(tier, is_quantum),
                "hot_path_candidate_flag": tier in HOT_TIERS and not is_quantum,
                "batch_only_flag": batch_only,
                "quantum_batch_only_flag": is_quantum,
                "cacheable_flag": bool(packet.get("cacheable")),
                "incremental_update_suitable_flag": bool(packet.get("incremental_update_supported")),
                "replay_paper_only_flag": True,
                "benchmark_required_before_live_flag": True,
                "benchmark_fill_action_ref": benchmark_ref,
                "precompute_required_flag": bool(packet.get("precompute_allowed") is False or batch_only),
                "no_live_hot_path_authority_flag": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def latency_by_packet(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_packet_ref")): row for row in rows}


def _route(tier: str, is_quantum: bool) -> str:
    if is_quantum:
        return "QUANTUM_BATCH_PRECOMPUTE_ONLY_NO_LIVE_DEPENDENCY"
    if tier in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA"}:
        return "FUTURE_HOT_PATH_CANDIDATE_REPLAY_PAPER_ONLY_UNTIL_LATER_BENCHMARK"
    if tier == "TIER_2_VECTORIZED_FEATURE_FORMULA":
        return "VECTORIZED_PRECOMPUTE_OR_INCREMENTAL_REPLAY_PAPER_ROUTE"
    return "BATCH_PRECOMPUTE_REPLAY_PAPER_ROUTE"


def _cost(tier: str, is_quantum: bool) -> str:
    if is_quantum:
        return "QUANTUM_OR_HYBRID_BATCH_COST"
    if tier.startswith("TIER_0") or tier.startswith("TIER_1"):
        return "LOW"
    if tier.startswith("TIER_2"):
        return "MEDIUM"
    return "HIGH_BATCH"


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
