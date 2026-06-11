"""Confidence and integrity score helpers."""

from __future__ import annotations

from typing import Any

from .cost_model import numeric
from .normalization import clamp, round6


def confidence_metrics(
    confidence_row: dict[str, Any],
    point_in_time_row: dict[str, Any],
    no_lookahead_row: dict[str, Any],
) -> dict[str, float]:
    point = 1.0 if point_in_time_row.get("no_live_market_state_used") is True and point_in_time_row.get("no_settlement_leak_used") is True else 0.5
    lookahead = 1.0 if no_lookahead_row.get("no_lookahead_pass") is True else 0.0
    settlement = numeric(confidence_row, "settlement_assumption_confidence_score", 0.65)
    return {
        "result_confidence_score": round6(clamp(numeric(confidence_row, "result_confidence_score", 0.5))),
        "point_in_time_score": round6(point),
        "no_lookahead_score": round6(lookahead),
        "fill_quality_score": round6(clamp(numeric(confidence_row, "fill_quality_score", 0.5))),
        "settlement_confidence_score": round6(clamp(settlement)),
        "sample_depth_score": round6(clamp(numeric(confidence_row, "data_depth_score", 0.5))),
    }
