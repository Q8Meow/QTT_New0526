"""Deterministic overfit and false-discovery controls."""

from __future__ import annotations

from decimal import Decimal

from .models import dec, score


def compute_fdr_penalty(
    *,
    effective_trial_count: int,
    observed_edge_stability: Decimal,
    validation_gap: Decimal,
    calibration_gap: Decimal,
    net_expected_pnl_cash: Decimal,
) -> Decimal:
    trial_penalty = dec(effective_trial_count).ln() * Decimal("0.002") if effective_trial_count > 1 else Decimal("0")
    instability_penalty = max(Decimal("0"), Decimal("1") - observed_edge_stability) * Decimal("0.030")
    gap_penalty = validation_gap.copy_abs() * Decimal("0.050") + calibration_gap.copy_abs() * Decimal("0.040")
    pnl_scaled = net_expected_pnl_cash.copy_abs() * Decimal("0.050")
    return trial_penalty + instability_penalty + gap_penalty + pnl_scaled


def fdr_summary(effective_trial_count: int, net_expected_pnl_cash: Decimal, calibration_gap: Decimal) -> dict[str, str]:
    penalty = compute_fdr_penalty(
        effective_trial_count=effective_trial_count,
        observed_edge_stability=Decimal("0.72"),
        validation_gap=Decimal("0.04"),
        calibration_gap=calibration_gap,
        net_expected_pnl_cash=net_expected_pnl_cash,
    )
    return {
        "fdr_penalty_cash": score(penalty),
        "adjusted_pnl_after_fdr_cash": score(net_expected_pnl_cash - penalty),
        "fdr_q_value_candidate": score("0.100000"),
    }

