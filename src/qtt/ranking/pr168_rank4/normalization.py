"""Deterministic robust normalization for PR168-RANK4."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .models import bounded, dec


def minmax(values: Iterable[Decimal], value: Decimal, *, higher_is_better: bool = True) -> Decimal:
    vals = list(values)
    if not vals:
        return Decimal("0")
    low = min(vals)
    high = max(vals)
    if high == low:
        normalized = Decimal("0.5")
    else:
        normalized = (value - low) / (high - low)
    if not higher_is_better:
        normalized = Decimal("1") - normalized
    return bounded(normalized)


def quality_from_penalty(penalty: object, denominator: object) -> Decimal:
    denom = max(abs(dec(denominator)), Decimal("0.000001"))
    return bounded(Decimal("1") - bounded(dec(penalty) / denom))

