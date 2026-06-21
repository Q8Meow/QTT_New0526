#!/usr/bin/env python3
"""Public read-only Polymarket client for PR168-DATA1."""

from __future__ import annotations

import json
from typing import Any

from tools.pr168_data1_config import (
    POLYMARKET_CLOB_BASE_URL,
    POLYMARKET_DATA_BASE_URL,
    POLYMARKET_GAMMA_BASE_URL,
    polymarket_market_fetch_target_default,
    polymarket_price_history_interval_default,
)
from tools.pr168_data1_http_client import HttpResult, PublicHttpClient


class PolymarketPublicClient:
    def __init__(self, http: PublicHttpClient | None = None) -> None:
        self.http = http or PublicHttpClient()

    def fetch_public_data(self) -> dict[str, object]:
        results: dict[str, HttpResult] = {}
        results["markets"] = self.http.get_json(
            f"{POLYMARKET_GAMMA_BASE_URL}/markets",
            {"active": "true", "closed": "false", "limit": polymarket_market_fetch_target_default},
        )
        markets = _as_list(results["markets"].json_value, "markets")
        selected_market = _select_orderbook_market(markets)
        selected_token = _first_token_id(selected_market)
        if selected_token:
            results["book"] = self.http.get_json(f"{POLYMARKET_CLOB_BASE_URL}/book", {"token_id": selected_token})
            results["prices_history"] = self.http.get_json(
                f"{POLYMARKET_CLOB_BASE_URL}/prices-history",
                {"market": selected_token, "interval": polymarket_price_history_interval_default, "fidelity": 60},
            )
        if selected_market and selected_market.get("conditionId"):
            results["data_trades"] = self.http.get_json(
                f"{POLYMARKET_DATA_BASE_URL}/trades",
                {"market": selected_market.get("conditionId"), "limit": 5},
            )
        return {
            "venue": "polymarket",
            "selected_market": selected_market,
            "selected_token": selected_token,
            "results": results,
        }


def _as_list(value: object, key: str) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return [item for item in value[key] if isinstance(item, dict)]
    return []


def _select_orderbook_market(markets: list[dict[str, Any]]) -> dict[str, Any] | None:
    for market in markets:
        tokens = _parse_json_array(market.get("clobTokenIds"))
        if tokens and str(market.get("enableOrderBook", "true")).lower() != "false":
            return market
    return markets[0] if markets else None


def _first_token_id(market: dict[str, Any] | None) -> str | None:
    if not market:
        return None
    tokens = _parse_json_array(market.get("clobTokenIds"))
    return str(tokens[0]) if tokens else None


def _parse_json_array(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []
