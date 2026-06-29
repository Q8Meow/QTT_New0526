"""Adverse selection penalty helper for RP5G."""

from decimal import Decimal


def adverse_selection_penalty(expected_gross_pnl_cash: Decimal, rate: Decimal = Decimal("0.060000")) -> Decimal:
    return expected_gross_pnl_cash.copy_abs() * rate

