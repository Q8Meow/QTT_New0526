#!/usr/bin/env python3
"""Prediction-market probability helpers for candidate-only computations."""

from __future__ import annotations


def clamp_probability(value: float | None) -> float | None:
    if value is None:
        return None
    return round(max(0.0, min(1.0, float(value))), 6)


def market_implied_probability(entry_price: float | None, payout_value: float = 1.0) -> float | None:
    if entry_price is None or payout_value <= 0:
        return None
    return clamp_probability(float(entry_price) / float(payout_value))


def opposite_binary_price(price: float | None) -> float | None:
    if price is None:
        return None
    return clamp_probability(1.0 - float(price))
