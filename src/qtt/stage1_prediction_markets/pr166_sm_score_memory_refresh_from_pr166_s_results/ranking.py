"""Rank and rank-delta helpers."""

from __future__ import annotations

from .enums import RankDeltaReason


def assign_ranks(rows: list[dict[str, object]]) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -float(row["net_edge_after_costs"]),
            -float(row["refreshed_net_edge_score"]),
            -float(row["result_confidence_score"]),
            float(row["false_discovery_risk_adjustment"]),
            float(row["overfit_risk_adjustment"]),
            float(row["cost_drag_ratio"]),
            float(row["latency_drag_ratio"]),
            float(row["liquidity_drag_ratio"]),
            float(row["adverse_selection_ratio"]),
            float(row["crowding_penalty"]),
            float(row["correlation_cluster_penalty"]),
            -float(row["scenario_consistency_score"]),
            -float(row["scenario_transferability_score"]),
            -float(row["fill_quality_score"]),
            -float(row["settlement_confidence_score"]),
            -float(row["capacity_score"]),
            -float(row["quantum_priority_after_replay_paper"]),
            str(row["qku_id"]),
            str(row["formula_id"]),
            str(row["algorithm_id"]),
            str(row["candidate_packet_id"]),
            str(row["condition_fingerprint_id"]),
            str(row.get("row_id", row["candidate_packet_id"])),
        ),
    )
    return {str(row["candidate_packet_id"]): index for index, row in enumerate(ordered, start=1)}


def reason_for_delta(
    *,
    prior_rank: int | None,
    rank_delta: int | None,
    cost_drag_ratio: float,
    latency_drag_ratio: float,
    liquidity_drag_ratio: float,
    adverse_selection_ratio: float,
    false_discovery_risk: float,
    overfit_risk: float,
    capacity_score: float,
    crowding_penalty: float,
    quantum_priority_delta: float,
    repair_needed: bool,
) -> str:
    if prior_rank is None or rank_delta is None:
        return RankDeltaReason.NO_PRIOR_RANK_AVAILABLE_WITH_REASON.value
    if repair_needed:
        return RankDeltaReason.REPAIR_NEEDED.value
    if quantum_priority_delta <= -0.02 or quantum_priority_delta >= 0.02:
        return RankDeltaReason.QUANTUM_PRIORITY_CHANGED.value
    if false_discovery_risk >= 0.65:
        return RankDeltaReason.FALSE_DISCOVERY_RISK_INCREASED.value
    if overfit_risk >= 0.65:
        return RankDeltaReason.OVERFIT_RISK_INCREASED.value
    if capacity_score < 0.35:
        return RankDeltaReason.CAPACITY_LIMITED.value
    if crowding_penalty >= 0.35:
        return RankDeltaReason.CROWDING_INCREASED.value
    if cost_drag_ratio >= 1.0:
        return RankDeltaReason.COST_DETERIORATED.value
    if latency_drag_ratio >= 0.08:
        return RankDeltaReason.LATENCY_DETERIORATED.value
    if liquidity_drag_ratio >= 0.08:
        return RankDeltaReason.LIQUIDITY_DETERIORATED.value
    if adverse_selection_ratio >= 0.18:
        return RankDeltaReason.ADVERSE_SELECTION_DETERIORATED.value
    if rank_delta > 0:
        return RankDeltaReason.NET_EDGE_IMPROVED.value
    return RankDeltaReason.CONFIDENCE_DECAYED.value
