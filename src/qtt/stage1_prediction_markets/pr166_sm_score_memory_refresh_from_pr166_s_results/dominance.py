"""Dominance and downgrade classifications."""

from __future__ import annotations

from .enums import PrimaryClassification


def classify(
    *,
    net_edge_after_costs: float,
    prior_score: float,
    refreshed_score: float,
    cost_drag_ratio: float,
    latency_drag_ratio: float,
    liquidity_drag_ratio: float,
    adverse_selection_ratio: float,
    settlement_sensitivity_ratio: float,
    result_confidence_score: float,
    false_discovery_risk: float,
    overfit_risk: float,
    rank_instability: float,
    capacity_score: float,
    crowding_penalty: float,
    correlation_penalty: float,
    repair_priority_score: float,
    quantum_priority_delta: float,
) -> tuple[str, list[str], list[str], dict[str, float]]:
    secondary: list[str] = []
    reason_codes: list[str] = []

    def add(condition: bool, item: PrimaryClassification, reason: str) -> None:
        if condition:
            secondary.append(item.value)
            reason_codes.append(reason)

    add(cost_drag_ratio >= 1.0, PrimaryClassification.COST_DOMINATED, "COST_DRAG_RATIO_AT_OR_ABOVE_ONE")
    add(latency_drag_ratio >= 0.08, PrimaryClassification.LATENCY_DOMINATED, "LATENCY_DRAG_RATIO_HIGH")
    add(liquidity_drag_ratio >= 0.08, PrimaryClassification.LIQUIDITY_DOMINATED, "LIQUIDITY_DRAG_RATIO_HIGH")
    add(adverse_selection_ratio >= 0.18, PrimaryClassification.ADVERSE_SELECTION_DOMINATED, "ADVERSE_SELECTION_RATIO_HIGH")
    add(settlement_sensitivity_ratio >= 0.08, PrimaryClassification.SETTLEMENT_SENSITIVE, "SETTLEMENT_RATIO_HIGH")
    add(result_confidence_score < 0.55, PrimaryClassification.LOW_CONFIDENCE_RESULT, "RESULT_CONFIDENCE_BELOW_055")
    add(false_discovery_risk >= 0.65, PrimaryClassification.FALSE_DISCOVERY_RISK_HIGH, "FALSE_DISCOVERY_RISK_AT_OR_ABOVE_065")
    add(overfit_risk >= 0.65, PrimaryClassification.OVERFIT_RISK_HIGH, "OVERFIT_RISK_AT_OR_ABOVE_065")
    add(rank_instability >= 0.65, PrimaryClassification.RANK_INSTABILITY_HIGH, "RANK_INSTABILITY_AT_OR_ABOVE_065")
    add(capacity_score < 0.35, PrimaryClassification.CAPACITY_LIMITED, "CAPACITY_SCORE_BELOW_035")
    add(crowding_penalty >= 0.35, PrimaryClassification.CROWDING_DOMINATED, "CROWDING_PENALTY_AT_OR_ABOVE_035")
    add(correlation_penalty >= 0.35, PrimaryClassification.CORRELATION_DUPLICATE, "CORRELATION_PENALTY_AT_OR_ABOVE_035")
    add(repair_priority_score >= 0.50, PrimaryClassification.REPAIR_BEFORE_RETEST, "REPAIR_PRIORITY_AT_OR_ABOVE_050")
    add(quantum_priority_delta > 0.02, PrimaryClassification.QUANTUM_PRIORITY_INCREASED, "QUANTUM_PRIORITY_DELTA_POSITIVE")
    add(quantum_priority_delta < -0.02, PrimaryClassification.QUANTUM_PRIORITY_DECREASED, "QUANTUM_PRIORITY_DELTA_NEGATIVE")
    add(refreshed_score > prior_score, PrimaryClassification.NET_EDGE_IMPROVED, "REFRESHED_SCORE_ABOVE_PRIOR")
    add(refreshed_score < prior_score, PrimaryClassification.NET_EDGE_DECAYED, "REFRESHED_SCORE_BELOW_PRIOR")

    if not secondary:
        secondary.append(PrimaryClassification.NO_REFRESH_REQUIRED_WITH_COMPUTABLE_REASON.value)
        reason_codes.append("REFRESHED_SCORE_WITHIN_PRIOR_BAND_AND_NO_DOMINANCE_THRESHOLD")
    primary = secondary[0]
    evidence = {
        "net_edge_after_costs": net_edge_after_costs,
        "prior_score": prior_score,
        "refreshed_score": refreshed_score,
        "cost_drag_ratio": cost_drag_ratio,
        "latency_drag_ratio": latency_drag_ratio,
        "liquidity_drag_ratio": liquidity_drag_ratio,
        "adverse_selection_ratio": adverse_selection_ratio,
        "settlement_sensitivity_ratio": settlement_sensitivity_ratio,
        "false_discovery_risk": false_discovery_risk,
        "overfit_risk": overfit_risk,
        "rank_instability": rank_instability,
    }
    return primary, secondary, reason_codes, evidence
