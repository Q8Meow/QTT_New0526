"""Decision formulas for PR168-GFP."""

from __future__ import annotations


def lower_confidence_bound_edge(edge: float, standard_error: float, confidence_multiplier: float) -> float:
    return float(edge) - float(confidence_multiplier) * float(standard_error)


def positive_negative_decision(
    net_expected_pnl_candidate: float,
    lower_confidence_bound_edge: float,
    threshold: float,
    blocking_flags: list[str] | tuple[str, ...] | None = None,
) -> dict[str, object]:
    blockers = list(blocking_flags or [])
    if blockers:
        return {"decision": "COMPUTED_NEUTRAL_OR_ZERO_EDGE", "decision_reason": "BLOCKING_FLAGS_PRESENT", "blocking_flags": blockers}
    if float(net_expected_pnl_candidate) > float(threshold) and float(lower_confidence_bound_edge) > 0.0:
        return {"decision": "COMPUTED_POSITIVE_EDGE", "decision_reason": "PNL_AND_LCB_PASS", "blocking_flags": []}
    if float(net_expected_pnl_candidate) < -abs(float(threshold)) or float(lower_confidence_bound_edge) < 0.0:
        return {"decision": "COMPUTED_NEGATIVE_EDGE", "decision_reason": "PNL_OR_LCB_NEGATIVE", "blocking_flags": []}
    return {"decision": "COMPUTED_NEUTRAL_OR_ZERO_EDGE", "decision_reason": "WITHIN_THRESHOLD_OR_ZERO", "blocking_flags": []}


def no_trade_decision_reason(blocking_flags: list[str] | tuple[str, ...], terminal_reason: str | None = None) -> str:
    if terminal_reason:
        return terminal_reason
    if blocking_flags:
        return "NO_TRADE_DUE_TO_" + "_".join(str(flag) for flag in blocking_flags)
    return "NO_TRADE_REASON_NOT_TRIGGERED"
