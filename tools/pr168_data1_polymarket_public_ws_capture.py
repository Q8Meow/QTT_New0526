#!/usr/bin/env python3
"""Optional public Polymarket market WebSocket dependency probe."""

from __future__ import annotations

import importlib.util

from tools.pr168_data1_config import POLYMARKET_MARKET_WS_URL


def websocket_dependency_status() -> dict[str, object]:
    available = importlib.util.find_spec("websockets") is not None
    return {
        "websocket_url": POLYMARKET_MARKET_WS_URL,
        "public_market_channel_verified_from_docs": True,
        "dependency_name": "websockets",
        "dependency_available": available,
        "capture_mode_selected": "PUBLIC_WEBSOCKET" if available else "REST_POLL",
        "gap_code": None if available else "WS_DEPENDENCY_GAP_EXACT_REASON",
        "gap_reason": None
        if available
        else "The optional websockets package is not installed in the local runtime; DATA1 used public REST polling fallback.",
    }
