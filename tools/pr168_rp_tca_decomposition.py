#!/usr/bin/env python3
"""Transaction-cost decomposition for PR168-RP."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tools.pr168_rp_unit_basis_normalizer import decimal_number, decimal_to_float, non_negative


def compute_tca_components(tca_row: dict[str, Any], micro_row: dict[str, Any], ranking_row: dict[str, Any] | None = None) -> dict[str, float]:
    gross_edge = decimal_number(tca_row.get("gross_edge"), field="gross_edge")
    explicit_fee_cost = non_negative(tca_row.get("fee_cost_component"), field="fee_cost_component")
    spread_cost = non_negative(tca_row.get("spread_cost_component"), field="spread_cost_component")
    slippage_cost = non_negative(tca_row.get("slippage_cost_component"), field="slippage_cost_component")
    market_impact = non_negative(tca_row.get("market_impact_cost_component"), field="market_impact_cost_component")
    implementation_shortfall = non_negative(tca_row.get("implementation_shortfall_proxy"), field="implementation_shortfall_proxy")
    latency_decay = non_negative(tca_row.get("latency_cost_component"), field="latency_cost_component")
    liquidity_cost = non_negative(tca_row.get("liquidity_cost_component"), field="liquidity_cost_component")
    queue_nonfill_penalty = liquidity_cost / Decimal("2")
    partial_fill_penalty = liquidity_cost - queue_nonfill_penalty
    net_after_costs = decimal_number(tca_row.get("net_edge_after_costs"), field="net_edge_after_costs")
    net_after_adverse = decimal_number(
        tca_row.get("pr166_sm_net_edge_after_costs_with_adverse_selection_drag", net_after_costs),
        field="pr166_sm_net_edge_after_costs_with_adverse_selection_drag",
    )
    adverse_selection_penalty = max(net_after_costs - net_after_adverse, Decimal("0"))
    ranking_row = ranking_row or {}
    capacity_crowding_penalty = non_negative(ranking_row["crowding_penalty"], field="crowding_penalty")
    total_tca = (
        explicit_fee_cost
        + spread_cost
        + slippage_cost
        + market_impact
        + adverse_selection_penalty
        + implementation_shortfall
        + latency_decay
        + queue_nonfill_penalty
        + partial_fill_penalty
        + capacity_crowding_penalty
    )
    return {
        "gross_edge": decimal_to_float(gross_edge),
        "explicit_fee_cost": decimal_to_float(explicit_fee_cost),
        "spread_cost": decimal_to_float(spread_cost),
        "slippage_cost": decimal_to_float(slippage_cost),
        "market_impact": decimal_to_float(market_impact),
        "adverse_selection_penalty": decimal_to_float(adverse_selection_penalty),
        "implementation_shortfall": decimal_to_float(implementation_shortfall),
        "latency_decay": decimal_to_float(latency_decay),
        "queue_nonfill_penalty": decimal_to_float(queue_nonfill_penalty),
        "partial_fill_penalty": decimal_to_float(partial_fill_penalty),
        "stale_orderbook_penalty": decimal_to_float(_stale_book_penalty(micro_row)),
        "capacity_crowding_penalty": decimal_to_float(capacity_crowding_penalty),
        "total_tca": decimal_to_float(total_tca),
    }


def _stale_book_penalty(micro_row: dict[str, Any]) -> Decimal:
    ttl = non_negative(micro_row.get("quote_staleness_ttl_ms", 0), field="quote_staleness_ttl_ms")
    return Decimal("0") if ttl <= Decimal("5000") else (ttl - Decimal("5000")) / Decimal("1000000")
