"""PR162C deterministic calibration formula deltas."""

from __future__ import annotations


def forecast_sharpness_candidate(probabilities: list[float] | tuple[float, ...]) -> float:
    values = [float(value) for value in probabilities]
    if not values:
        raise ValueError("probabilities must not be empty")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("probabilities must be in [0, 1]")
    return sum(abs(value - 0.5) for value in values) / len(values)


def reliability_bin_calibration_candidate(
    predicted_probabilities: list[float] | tuple[float, ...],
    observed_outcomes: list[int] | tuple[int, ...],
) -> float:
    preds = [float(value) for value in predicted_probabilities]
    outcomes = [int(value) for value in observed_outcomes]
    if not preds or len(preds) != len(outcomes):
        raise ValueError("predicted probabilities and outcomes must have equal non-zero length")
    if any(value < 0.0 or value > 1.0 for value in preds):
        raise ValueError("predicted probabilities must be in [0, 1]")
    if any(value not in (0, 1) for value in outcomes):
        raise ValueError("observed outcomes must be 0 or 1")
    return abs(sum(preds) / len(preds) - sum(outcomes) / len(outcomes))
