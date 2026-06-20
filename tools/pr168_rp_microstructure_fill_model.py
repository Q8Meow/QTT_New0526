#!/usr/bin/env python3
"""Prediction-market microstructure and fill features for PR168-RP."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tools.pr168_rp_unit_basis_normalizer import decimal_to_float, non_negative


def compute_microstructure_features(micro_row: dict[str, Any], side: str) -> dict[str, Any]:
    side_norm = str(side or "YES").upper()
    bid_field = "best_bid_yes_cents" if side_norm == "YES" else "best_bid_no_cents"
    ask_field = "best_ask_yes_cents" if side_norm == "YES" else "best_ask_no_cents"
    bid = non_negative(micro_row[bid_field], field=bid_field) / Decimal("100")
    ask = non_negative(micro_row[ask_field], field=ask_field) / Decimal("100")
    depth_top_1 = non_negative(micro_row["order_book_depth_top_1"], field="order_book_depth_top_1")
    depth_top_5 = non_negative(micro_row["order_book_depth_top_5"], field="order_book_depth_top_5")
    depth_top_10 = non_negative(micro_row["order_book_depth_top_10"], field="order_book_depth_top_10")
    fill_probability = non_negative(micro_row["expected_fill_probability_proxy"], field="expected_fill_probability_proxy")
    if fill_probability > Decimal("1"):
        raise ValueError("expected_fill_probability_proxy must be in [0, 1]")
    midpoint = (bid + ask) / Decimal("2")
    spread = max(ask - bid, Decimal("0"))
    return {
        "venue": micro_row.get("venue", "VENUE_NEUTRAL_SYNTHETIC_FIXTURE"),
        "market_id": micro_row.get("market_id"),
        "token_id": None,
        "bid_depth": decimal_to_float(depth_top_1),
        "ask_depth": decimal_to_float(depth_top_1),
        "visible_depth": decimal_to_float(depth_top_5),
        "top_of_book_bid": decimal_to_float(bid),
        "top_of_book_ask": decimal_to_float(ask),
        "midpoint": decimal_to_float(midpoint),
        "spread": decimal_to_float(spread),
        "order_quantity": decimal_to_float(non_negative(micro_row["min_trade_size_candidate"], field="min_trade_size_candidate")),
        "queue_ahead": decimal_to_float(depth_top_1 * (Decimal("1") - non_negative(micro_row["queue_position_proxy_score"], field="queue_position_proxy_score"))),
        "book_timestamp": "MISSING_BOOK_TIMESTAMP_ROUTED_TO_INPUT_GAP",
        "book_staleness": int(non_negative(micro_row["quote_staleness_ttl_ms"], field="quote_staleness_ttl_ms")),
        "fill_intensity": decimal_to_float(fill_probability * depth_top_10),
        "fill_probability": decimal_to_float(fill_probability),
        "partial_fill_ratio": decimal_to_float(fill_probability),
        "no_fill_opportunity_cost": decimal_to_float((Decimal("1") - fill_probability) * spread),
        "stale_book_penalty": decimal_to_float(Decimal("0") if int(micro_row["quote_staleness_ttl_ms"]) <= 5000 else Decimal(str(int(micro_row["quote_staleness_ttl_ms"]) - 5000)) / Decimal("1000000")),
        "time_horizon": "REPLAY_PAPER_SCENARIO_WINDOW",
        "time_to_resolution_bucket": micro_row.get("time_to_resolution_bucket", "UNKNOWN_TIME_TO_RESOLUTION_BUCKET"),
        "spread_bucket": micro_row.get("spread_bucket"),
        "liquidity_bucket": micro_row.get("liquidity_bucket"),
        "latency_bucket": micro_row.get("latency_bucket"),
        "fill_regime_bucket": _fill_regime(float(fill_probability)),
        "capacity_limit": decimal_to_float(depth_top_5),
        "crowding_score": micro_row.get("capacity_bucket"),
        "order_type_candidate": "LIMIT_CANDIDATE",
        "limit_price_candidate": decimal_to_float(ask),
        "worst_price_limit_candidate": decimal_to_float(ask),
        "slippage_protection_candidate": decimal_to_float(spread),
        "microstructure_input_gap_route": "PR168_RP_MissingValueCandidateFillQueue.report.json",
    }


def _fill_regime(fill_probability: float) -> str:
    if fill_probability >= 0.75:
        return "HIGH_FILL_PROBABILITY"
    if fill_probability >= 0.55:
        return "MEDIUM_FILL_PROBABILITY"
    return "LOW_FILL_PROBABILITY"
