"""Condition-scoped memory refresh logic."""

from __future__ import annotations

from .enums import MemoryOutcome, PrimaryClassification


def memory_outcome(primary: str, refreshed_score: float, net_edge_after_costs: float) -> str:
    if primary == PrimaryClassification.COST_DOMINATED.value:
        return MemoryOutcome.COST_DOMINATED_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.LATENCY_DOMINATED.value:
        return MemoryOutcome.LATENCY_DOMINATED_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.LIQUIDITY_DOMINATED.value:
        return MemoryOutcome.LIQUIDITY_DOMINATED_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.ADVERSE_SELECTION_DOMINATED.value:
        return MemoryOutcome.ADVERSE_SELECTION_DOMINATED_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.FALSE_DISCOVERY_RISK_HIGH.value:
        return MemoryOutcome.FALSE_DISCOVERY_RISK_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.OVERFIT_RISK_HIGH.value:
        return MemoryOutcome.OVERFIT_RISK_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.RANK_INSTABILITY_HIGH.value:
        return MemoryOutcome.RANK_INSTABILITY_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.SETTLEMENT_SENSITIVE.value:
        return MemoryOutcome.SETTLEMENT_SENSITIVE_UNDER_MATCHING_CONDITIONS.value
    if primary == PrimaryClassification.CAPACITY_LIMITED.value:
        return MemoryOutcome.CAPACITY_LIMITED_UNDER_MATCHING_CONDITIONS.value
    if primary in {
        PrimaryClassification.REPAIR_BEFORE_RETEST.value,
        PrimaryClassification.QUANTUM_PRIORITY_INCREASED.value,
    }:
        return MemoryOutcome.REPAIR_BEFORE_RETEST_UNDER_MATCHING_CONDITIONS.value
    if refreshed_score >= 0.62 and net_edge_after_costs >= -0.02:
        return MemoryOutcome.PREFER_UNDER_MATCHING_CONDITIONS.value
    if refreshed_score <= 0.35 or net_edge_after_costs < -0.18:
        return MemoryOutcome.AVOID_UNDER_MATCHING_CONDITIONS.value
    if refreshed_score >= 0.48:
        return MemoryOutcome.WATCH_UNDER_MATCHING_CONDITIONS.value
    return MemoryOutcome.NO_MEMORY_CHANGE_WITH_COMPUTABLE_REASON.value
