"""Kalshi paper adapter capability declarations."""

from __future__ import annotations

from .paper_adapter_interface import capability_row


def build_capability_row(index: int = 1) -> dict:
    return capability_row(
        index,
        "KALSHI_PREDICTION_MARKETS",
        [
            "demo_environment_separated_from_live_exchange",
            "orderbook_market_data_candidate_semantics",
            "REST_WebSocket_FIX_source_slots",
            "no_api_key_use",
            "no_live_submission",
        ],
        [
            "https://docs.kalshi.com/welcome",
            "https://docs.kalshi.com/llms.txt",
        ],
    )
