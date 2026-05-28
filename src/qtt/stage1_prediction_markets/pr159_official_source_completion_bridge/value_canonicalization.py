"""Value canonicalization helpers for PR159 accepted source packets."""

from __future__ import annotations

from typing import Any


def canonicalization_required(value: Any, unit_or_basis: str | None, scale: str | None) -> bool:
    return value is not None and bool(unit_or_basis) and bool(scale)


__all__ = ["canonicalization_required"]

