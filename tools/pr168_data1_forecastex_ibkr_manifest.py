#!/usr/bin/env python3
"""ForecastEx/IBKR auth-required manifest rows for DATA1."""

from __future__ import annotations

from tools.pr168_data1_config import authority_flags, route_defaults


def forecastex_ibkr_rows(now_utc: str) -> list[dict[str, object]]:
    route = route_defaults("governance")
    return [
        {
            "forecast_ex_ibkr_row_id": "forecastex_ibkr_auth_required_0001",
            "venue": "forecastex_ibkr",
            "data_family": "event_contract_market_data",
            "data_readiness_state": "AUTH_REQUIRED_PENDING_OWNER_SETUP",
            "orderbook_state": "MARKET_DATA_SUBSCRIPTION_REQUIRED",
            "historical_data_state": "MARKET_DATA_SUBSCRIPTION_REQUIRED",
            "conid_required": True,
            "private_state_default": "BLOCKED",
            "order_authority_default": "BLOCKED",
            "source_urls": [
                "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
                "https://interactivebrokers.github.io/tws-api/market_data.html",
                "https://interactivebrokers.github.io/tws-api/historical_data.html",
            ],
            "owner_setup_route": "OWNER_IBKR_SETUP",
            "created_at_utc": now_utc,
            **route,
            **authority_flags(),
        }
    ]
