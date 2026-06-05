"""Venue-specific binding maps for PR162R-B."""

from __future__ import annotations

from typing import Any

from .binding_family_classifier import VENUE_SCOPES


def build_venue_binding_maps(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bindings_by_venue = {
        venue: sorted(
            binding["binding_id"]
            for binding in dataset_bindings
            if binding["venue_scope"] == venue
        )
        for venue in VENUE_SCOPES
    }
    rows = []
    for venue in VENUE_SCOPES:
        rows.append(
            {
                "venue_binding_map_id": f"PR162R_B_VENUE_BINDING_MAP::{len(rows) + 1:03d}",
                "venue_scope": venue,
                "binding_refs": bindings_by_venue[venue],
                "market_metadata_binding": "separate",
                "event_lifecycle_binding": "separate",
                "contract_or_token_lifecycle_binding": "separate",
                "orderbook_snapshot_binding": "separate",
                "trade_print_binding": "separate",
                "settlement_label_binding": "separate",
                "fee_slippage_model_binding": "separate",
                "paper_or_demo_environment_binding": "synthetic_fixture_only",
                "source_locator_candidates": _source_locators(venue),
                "trade_direction_caution": (
                    "Polymarket feed-inferred trade direction remains candidate-only unless cross-checked with on-chain fill records"
                    if venue == "POLYMARKET_CLOB"
                    else ""
                ),
                "no_live_connector_binding": True,
                "no_private_account_wallet_cash_state": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _source_locators(venue: str) -> list[str]:
    if venue == "KALSHI_PREDICTION_MARKETS":
        return [
            "https://docs.kalshi.com/welcome",
            "https://docs.kalshi.com/api-reference/market/get-multiple-market-orderbooks",
            "Kalshi REST/WebSocket/FIX documentation locator candidate",
        ]
    if venue == "POLYMARKET_CLOB":
        return [
            "https://docs.polymarket.com/trading/overview",
            "https://docs.polymarket.com/resources/blockchain-data",
            "Polymarket WebSocket and CLOB data-resource locator candidate",
        ]
    if venue == "FORECASTEX_IBKR_EVENT_MARKETS":
        return [
            "https://www.interactivebrokers.com/en/pricing/commissions-events.php",
            "IBKR TWS/Web API/FIX documentation locator candidate",
        ]
    return [
        "tests/fixtures/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion",
    ]
