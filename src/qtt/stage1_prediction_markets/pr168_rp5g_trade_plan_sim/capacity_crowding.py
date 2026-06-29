"""Capacity and crowding penalties."""

from __future__ import annotations

from decimal import Decimal

from .models import dec, score


def compute_capacity_penalty(order_size_contracts: int, depth_bucket: str, liquidity_bucket: str) -> Decimal:
    size = dec(order_size_contracts)
    depth_rate = {"HIGH": Decimal("0.001"), "MEDIUM": Decimal("0.003"), "LOW": Decimal("0.010"), "THIN": Decimal("0.018"), "BLOCKED": Decimal("0.050")}.get(depth_bucket, Decimal("0.012"))
    liq_rate = {"HIGH": Decimal("0.001"), "MEDIUM": Decimal("0.003"), "LOW": Decimal("0.012"), "BLOCKED": Decimal("0.050")}.get(liquidity_bucket, Decimal("0.010"))
    return size * (depth_rate + liq_rate)


def compute_crowding_penalty(near_clone_count: int, formula_family_count: int, venue_cluster_count: int) -> Decimal:
    return dec(near_clone_count) * Decimal("0.015") + dec(formula_family_count) * Decimal("0.005") + dec(venue_cluster_count) * Decimal("0.004")


def capacity_crowding_summary(order_size_contracts: int, depth_bucket: str, liquidity_bucket: str, near_clone_count: int = 1) -> dict[str, str]:
    capacity = compute_capacity_penalty(order_size_contracts, depth_bucket, liquidity_bucket)
    crowding = compute_crowding_penalty(near_clone_count, 1, 1)
    return {
        "capacity_penalty_cash": score(capacity),
        "crowding_penalty_cash": score(crowding),
        "capacity_crowding_penalty_cash": score(capacity + crowding),
    }

