"""Eligibility gates for PR168-RANK4 advisory champion previews."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import dec
from .policy import policy_value


def no_trade_required_margin(tca_total_cash: Decimal) -> Decimal:
    return max(Decimal("0"), Decimal("0.10") * abs(tca_total_cash))


def champion_gate(feature: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    threshold = no_trade_required_margin(dec(feature.get("TCA_total_cash")))
    if dec(feature.get("candidate_minus_no_trade_cash")) <= threshold:
        reasons.append("NO_TRADE_MARGIN_NOT_MET")
    if dec(feature.get("lower_confidence_bound_pnl_cash")) <= policy_value("lcb_min_cash_default"):
        reasons.append("LCB_NOT_POSITIVE")
    if dec(feature.get("fdr_adjusted_expected_pnl_cash")) <= Decimal("0"):
        reasons.append("FDR_ADJUSTED_PNL_NOT_POSITIVE")
    if feature.get("scenario_combined_conservative_pass_flag") is not True:
        reasons.append("SCENARIO_CONSERVATIVE_FAIL")
    if dec(feature.get("fill_probability")) < policy_value("min_fill_probability_for_champion_preview_default"):
        reasons.append("FILL_PROBABILITY_TOO_LOW")
    if dec(feature.get("capacity_crowding_penalty_cash")) > policy_value("max_capacity_crowding_penalty_cash_default"):
        reasons.append("CAPACITY_CROWDING_TOO_HIGH")
    if dec(feature.get("calibration_gap")) > policy_value("max_calibration_gap_default"):
        reasons.append("CALIBRATION_GAP_TOO_HIGH")
    if dec(feature.get("portfolio_marginal_utility_cash")) < policy_value("min_portfolio_utility_for_champion_preview_default"):
        reasons.append("PORTFOLIO_UTILITY_TOO_LOW")
    if feature.get("agent_route_pass_flag") is not True:
        reasons.append("AGENT_ROUTE_MISSING")
    if feature.get("no_orphan_proof_pass_flag") is not True:
        reasons.append("NO_ORPHAN_PROOF_MISSING")
    return not reasons, reasons

