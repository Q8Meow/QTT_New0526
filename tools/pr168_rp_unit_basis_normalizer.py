#!/usr/bin/env python3
"""Unit, basis, sign, and finite-number checks for PR168-RP."""

from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation
from typing import Any


def decimal_number(value: Any, *, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} is not numeric: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def bounded_probability(value: Any, *, field: str) -> Decimal:
    result = decimal_number(value, field=field)
    if result < Decimal("0") or result > Decimal("1"):
        raise ValueError(f"{field} must be in [0, 1]")
    return result


def cents_to_probability(cents: Any, *, field: str) -> Decimal:
    value = decimal_number(cents, field=field) / Decimal("100")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field} cents must normalize into [0, 1]")
    return value


def non_negative(value: Any, *, field: str) -> Decimal:
    result = decimal_number(value, field=field)
    if result < Decimal("0"):
        raise ValueError(f"{field} must be non-negative")
    return result


def decimal_to_float(value: Decimal) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("numeric output must be finite")
    return round(result, 10)
