"""Fill, queue, partial-fill, and latency formulas for PR168-GFP."""

from __future__ import annotations

import math


def queue_fill_probability(
    fill_intensity: float,
    time_horizon: float,
    queue_ahead: float,
    order_quantity: float,
) -> float:
    denominator = max(float(queue_ahead) + float(order_quantity), 1e-12)
    probability = 1.0 - math.exp(-float(fill_intensity) * float(time_horizon) / denominator)
    return max(0.0, min(1.0, probability))


def partial_fill(filled_quantity: float, requested_quantity: float) -> float:
    requested = max(float(requested_quantity), 1e-12)
    return max(0.0, min(1.0, float(filled_quantity) / requested))
