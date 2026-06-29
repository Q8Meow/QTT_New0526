"""Calibration proxy calculations."""

from __future__ import annotations

from decimal import Decimal

from .models import score


def calibration_gap(estimated_probability: Decimal, calibrated_probability: Decimal) -> Decimal:
    return (estimated_probability - calibrated_probability).copy_abs()


def brier_score(estimated_probability: Decimal, outcome_proxy: Decimal) -> Decimal:
    diff = estimated_probability - outcome_proxy
    return diff * diff


def calibration_summary(estimated_probability: Decimal, calibrated_probability: Decimal) -> dict[str, str]:
    gap = calibration_gap(estimated_probability, calibrated_probability)
    return {
        "calibration_gap": score(gap),
        "brier_score_proxy": score(brier_score(estimated_probability, calibrated_probability)),
        "calibration_penalty_cash": score(gap * Decimal("0.100000")),
    }

