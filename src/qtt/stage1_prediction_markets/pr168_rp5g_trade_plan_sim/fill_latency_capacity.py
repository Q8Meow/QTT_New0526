"""Fill, queue, latency, and capacity adjustment formulas."""

from __future__ import annotations

from decimal import Decimal

from .models import clamp, dec, score


def fill_probability_for(liquidity_bucket: str, maker_taker_policy: str) -> Decimal:
    base = {"HIGH": Decimal("0.92"), "MEDIUM": Decimal("0.76"), "LOW": Decimal("0.48"), "BLOCKED": Decimal("0.00")}.get(liquidity_bucket, Decimal("0.55"))
    adjustment = {
        "MAKER_ONLY": Decimal("-0.10"),
        "TAKER_ONLY": Decimal("0.06"),
        "MAKER_THEN_TAKER": Decimal("0.03"),
        "SPLIT_50_50": Decimal("0.00"),
        "POST_ONLY_WITH_CANCEL_REPLACE": Decimal("-0.08"),
        "TAKER_AFTER_TIMEOUT": Decimal("0.02"),
    }.get(maker_taker_policy, Decimal("0"))
    return clamp(base + adjustment)


def partial_fill_ratio_for(depth_bucket: str, order_size_contracts: int) -> Decimal:
    depth_cap = {"HIGH": Decimal("100"), "MEDIUM": Decimal("50"), "THIN": Decimal("15"), "LOW": Decimal("20"), "BLOCKED": Decimal("0")}.get(depth_bucket, Decimal("20"))
    if order_size_contracts <= 0:
        return Decimal("0")
    return clamp(depth_cap / dec(order_size_contracts))


def latency_decay_penalty(alpha_decay_per_ms: Decimal, latency_ms: int, order_size_contracts: int) -> Decimal:
    return alpha_decay_per_ms * dec(latency_ms) * dec(order_size_contracts)


def fill_adjusted_expected_pnl(expected_gross_pnl_cash: Decimal, tca_total_cash: Decimal, fill_probability: Decimal, partial_fill_ratio: Decimal) -> Decimal:
    return fill_probability * partial_fill_ratio * expected_gross_pnl_cash - tca_total_cash


def adjustment_summary(
    *,
    expected_gross_pnl_cash: Decimal,
    tca_total_cash: Decimal,
    liquidity_bucket: str,
    depth_bucket: str,
    maker_taker_policy: str,
    latency_ms: int,
    order_size_contracts: int,
    alpha_decay_per_ms: Decimal = Decimal("0.000004"),
) -> dict[str, str]:
    fill_prob = fill_probability_for(liquidity_bucket, maker_taker_policy)
    partial = partial_fill_ratio_for(depth_bucket, order_size_contracts)
    lat_penalty = latency_decay_penalty(alpha_decay_per_ms, latency_ms, order_size_contracts)
    fill_pnl = fill_adjusted_expected_pnl(expected_gross_pnl_cash, tca_total_cash, fill_prob, partial)
    return {
        "fill_probability": score(fill_prob),
        "partial_fill_ratio": score(partial),
        "latency_decay_penalty_cash": score(lat_penalty),
        "fill_adjusted_expected_pnl_cash": score(fill_pnl),
        "latency_adjusted_expected_pnl_cash": score(fill_pnl - lat_penalty),
    }

