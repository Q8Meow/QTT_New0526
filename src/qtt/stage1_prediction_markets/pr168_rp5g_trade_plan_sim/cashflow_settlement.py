"""Cashflow and settlement proxy helper for RP5G."""

from decimal import Decimal


def capital_lock_cost(order_size_contracts: int, hold_hours: Decimal, rate_per_hour: Decimal = Decimal("0.000010")) -> Decimal:
    return Decimal(order_size_contracts) * hold_hours * rate_per_hour

