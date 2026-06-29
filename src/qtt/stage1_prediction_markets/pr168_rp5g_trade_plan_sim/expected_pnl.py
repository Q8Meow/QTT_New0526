"""Expected PnL and confidence formulas for RP5G."""

from __future__ import annotations

from decimal import Decimal

from .models import clamp, dec, score


def normalize_price(value: int | float | str | Decimal, *, source_uses_cents: bool = False) -> Decimal:
    raw = dec(value)
    if source_uses_cents:
        raw = raw / Decimal("100")
    return clamp(raw)


def gross_edge_per_contract(estimated_fair_probability_dec: Decimal, entry_price_dec: Decimal) -> Decimal:
    return estimated_fair_probability_dec - entry_price_dec


def expected_gross_pnl_cash(order_size_contracts: int | Decimal, payout_per_contract_cash: Decimal, gross_edge: Decimal) -> Decimal:
    return dec(order_size_contracts) * payout_per_contract_cash * gross_edge


def lower_confidence_bound_pnl(net_expected_pnl_cash: Decimal, z_value: Decimal, estimated_pnl_std_cash: Decimal) -> Decimal:
    return net_expected_pnl_cash - z_value * estimated_pnl_std_cash


def binary_expected_pnl_summary(
    *,
    entry_price_dec: Decimal,
    estimated_fair_probability_dec: Decimal,
    order_size_contracts: int,
    payout_per_contract_cash: Decimal = Decimal("1.00"),
    z_value: Decimal = Decimal("1.645"),
    estimated_pnl_std_cash: Decimal = Decimal("0.05"),
) -> dict[str, str]:
    edge = gross_edge_per_contract(estimated_fair_probability_dec, entry_price_dec)
    gross = expected_gross_pnl_cash(order_size_contracts, payout_per_contract_cash, edge)
    return {
        "gross_edge_per_contract": score(edge),
        "expected_gross_pnl_cash": score(gross),
        "lower_confidence_bound_before_cost_cash": score(lower_confidence_bound_pnl(gross, z_value, estimated_pnl_std_cash)),
    }

