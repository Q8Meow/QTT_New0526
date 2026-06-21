#!/usr/bin/env python3
"""Public read-only Kalshi client for PR168-DATA1."""

from __future__ import annotations

import time
from typing import Any

from tools.pr168_data1_config import (
    KALSHI_BASE_URL,
    kalshi_market_fetch_target_default,
)
from tools.pr168_data1_http_client import HttpResult, PublicHttpClient


class KalshiPublicClient:
    def __init__(self, http: PublicHttpClient | None = None) -> None:
        self.http = http or PublicHttpClient()

    def fetch_public_data(self) -> dict[str, object]:
        results: dict[str, HttpResult] = {}
        results["markets"] = self.http.get_json(
            f"{KALSHI_BASE_URL}/markets",
            {"limit": kalshi_market_fetch_target_default, "status": "open"},
        )
        markets = _as_list(results["markets"].json_value, "markets")
        selected_market = self._select_market_with_book(markets, results)
        if selected_market:
            ticker = str(selected_market.get("ticker", ""))
            series_ticker = str(selected_market.get("series_ticker") or ticker.split("-")[0])
            now_ts = int(time.time())
            results["candlesticks"] = self.http.get_json(
                f"{KALSHI_BASE_URL}/series/{series_ticker}/markets/{ticker}/candlesticks",
                {"start_ts": now_ts - 86400, "end_ts": now_ts, "period_interval": 60},
            )
        results["market_trades"] = self.http.get_json(f"{KALSHI_BASE_URL}/markets/trades", {"limit": 5})
        results["historical_cutoff"] = self.http.get_json(f"{KALSHI_BASE_URL}/historical/cutoff")
        results["historical_trades"] = self.http.get_json(f"{KALSHI_BASE_URL}/historical/trades", {"limit": 5})
        return {
            "venue": "kalshi",
            "selected_market": selected_market,
            "results": results,
        }

    def _select_market_with_book(
        self,
        markets: list[dict[str, Any]],
        results: dict[str, HttpResult],
    ) -> dict[str, Any] | None:
        fallback = markets[0] if markets else None
        for index, market in enumerate(markets[:25]):
            ticker = str(market.get("ticker", ""))
            if not ticker:
                continue
            result = self.http.get_json(f"{KALSHI_BASE_URL}/markets/{ticker}/orderbook")
            results[f"orderbook_{index}"] = result
            if _has_depth(result.json_value):
                return market
        if fallback:
            ticker = str(fallback.get("ticker", ""))
            if ticker and not any(key.startswith("orderbook_") for key in results):
                results["orderbook_0"] = self.http.get_json(f"{KALSHI_BASE_URL}/markets/{ticker}/orderbook")
        return fallback


def _as_list(value: object, key: str) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return [item for item in value[key] if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _has_depth(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    orderbook = value.get("orderbook_fp") or value.get("orderbook")
    if not isinstance(orderbook, dict):
        return False
    yes_levels = orderbook.get("yes_dollars") or orderbook.get("yes") or []
    no_levels = orderbook.get("no_dollars") or orderbook.get("no") or []
    return bool(yes_levels or no_levels)
