"""Repair-priority scoring and route selection."""

from __future__ import annotations

from typing import Any

from .enums import RepairRoute
from .normalization import clamp, round6


def repair_priority_score(
    *,
    refreshed_score: float,
    prior_rank_percentile: float,
    net_edge_after_costs: float,
    false_discovery_risk: float,
    overfit_risk: float,
    quantum_readiness: float,
    formula_missing: bool,
    repair_route_present: bool,
) -> float:
    positive = (
        0.28 * refreshed_score
        + 0.20 * prior_rank_percentile
        + 0.18 * quantum_readiness
        + (0.16 if formula_missing else 0.0)
        + (0.12 if repair_route_present else 0.0)
        + (0.06 if net_edge_after_costs > -0.05 else 0.0)
    )
    negative = 0.20 * false_discovery_risk + 0.18 * overfit_risk + (0.18 if net_edge_after_costs < -0.25 else 0.0)
    return round6(clamp(positive - negative))


def repair_route(*, formula_missing: bool, quantum_readiness: float, structurally_negative: bool, high_potential: bool) -> str:
    if structurally_negative and not high_potential:
        return RepairRoute.TERMINAL_BY_NATURE_WITH_REASON.value
    if quantum_readiness >= 0.62:
        return RepairRoute.PR162E_Q.value
    if formula_missing:
        return RepairRoute.PR162E.value
    if high_potential:
        return RepairRoute.PR166_SF.value
    return RepairRoute.PR167.value
