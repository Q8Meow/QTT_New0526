"""Calibration formula implementations for PR162B."""

from __future__ import annotations

import math


def _require_probability(value: float, name: str) -> float:
    result = float(value)
    if result < 0.0 or result > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def brier_score_binary(y_true: int, p_pred: float) -> float:
    if y_true not in (0, 1):
        raise ValueError("y_true must be 0 or 1")
    p = _require_probability(p_pred, "p_pred")
    return (float(y_true) - p) ** 2


def probability_clipping(probability: float, epsilon: float) -> float:
    p = _require_probability(probability, "probability")
    eps = float(epsilon)
    if eps <= 0.0 or eps >= 0.5:
        raise ValueError("epsilon must be in (0, 0.5)")
    return min(max(p, eps), 1.0 - eps)


def log_loss_binary(y_true: int, p_pred: float, epsilon: float = 1e-15) -> float:
    if y_true not in (0, 1):
        raise ValueError("y_true must be 0 or 1")
    p = probability_clipping(p_pred, epsilon)
    return -math.log(p if y_true == 1 else 1.0 - p)


def calibration_error_candidate(observed_probability: float, predicted_probability: float) -> float:
    return abs(
        _require_probability(observed_probability, "observed_probability")
        - _require_probability(predicted_probability, "predicted_probability")
    )


def confidence_penalty_candidate(confidence: float, penalty_weight: float) -> float:
    c = _require_probability(confidence, "confidence")
    return float(penalty_weight) * (1.0 - c)
