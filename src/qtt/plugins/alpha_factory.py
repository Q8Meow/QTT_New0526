"""Alpha recovery arithmetic for nonlive repair ranking."""

from __future__ import annotations


def expected_alpha_recovery(
    *,
    expected_repair_value: float,
    expected_retest_value: float,
    repair_uncertainty_penalty: float,
) -> float:
    return round(
        float(expected_repair_value)
        + float(expected_retest_value)
        - float(repair_uncertainty_penalty),
        6,
    )
