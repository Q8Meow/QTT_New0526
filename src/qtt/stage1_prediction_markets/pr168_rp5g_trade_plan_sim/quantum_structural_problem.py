"""Quantum-forward structural problem construction without QOPT execution."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .models import score


def build_variable_names(candidate_ids: Iterable[str]) -> list[str]:
    names = []
    for candidate_id in candidate_ids:
        safe = candidate_id.lower().replace("-", "_")
        names.append(f"x_{safe}_selected_binary")
    names.append("x_no_trade_binary")
    return names


def objective_coefficients(candidate_scores: dict[str, Decimal]) -> dict[str, str]:
    coeffs = {f"x_{cid.lower().replace('-', '_')}_selected_binary": score(value) for cid, value in candidate_scores.items()}
    coeffs["x_no_trade_binary"] = score(0)
    return coeffs


def structural_quality_score(variable_count: int, constraint_count: int, interpret_back_present: bool, fallback_present: bool) -> str:
    raw = Decimal("0.40") + Decimal(variable_count) * Decimal("0.015") + Decimal(constraint_count) * Decimal("0.020")
    if interpret_back_present:
        raw += Decimal("0.20")
    if fallback_present:
        raw += Decimal("0.20")
    return score(min(raw, Decimal("1.000000")))

