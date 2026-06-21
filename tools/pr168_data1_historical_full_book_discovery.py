#!/usr/bin/env python3
"""Historical full-book availability audit and candidate source ledger."""

from __future__ import annotations

from tools.pr168_data1_config import (
    THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATES,
    authority_flags,
    route_defaults,
)


def official_historical_full_book_audit(now_utc: str) -> list[dict[str, object]]:
    route = route_defaults("source_evidence")
    return [
        {
            "audit_row_id": "kalshi_official_historical_full_book_0001",
            "venue": "kalshi",
            "source_tier": "OFFICIAL_PUBLIC_API",
            "historical_full_book_state": "HISTORICAL_FULL_BOOK_UNAVAILABLE",
            "availability_classification": "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
            "exact_reason": (
                "Official Kalshi historical docs expose historical markets, trades, candlesticks, fills, orders, "
                "and cutoff. No public historical full-book/orderbook replay endpoint was found. Historical orders "
                "and orderbook WebSocket require authentication and are not used by DATA1 default."
            ),
            "public_substitute_data": ["current_orderbook_snapshot", "historical_trades", "candlesticks", "forward_rest_poll_capture"],
            "source_urls": [
                "https://docs.kalshi.com/getting_started/historical_data",
                "https://docs.kalshi.com/api-reference/historical/get-historical-orders",
                "https://docs.kalshi.com/websockets/orderbook-updates",
            ],
            "created_at_utc": now_utc,
            **route,
            **authority_flags(),
        },
        {
            "audit_row_id": "polymarket_official_historical_full_book_0001",
            "venue": "polymarket",
            "source_tier": "OFFICIAL_PUBLIC_API",
            "historical_full_book_state": "HISTORICAL_FULL_BOOK_UNAVAILABLE",
            "availability_classification": "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
            "exact_reason": (
                "Official Polymarket docs expose current CLOB book, price-history, Data API trades, and public market "
                "WebSocket for forward capture. No official public historical full-book/L2 replay endpoint or dataset "
                "was found in the public API docs."
            ),
            "public_substitute_data": ["current_clob_book", "prices_history", "public_data_trades", "forward_rest_or_ws_capture"],
            "source_urls": [
                "https://docs.polymarket.com/market-data/overview",
                "https://docs.polymarket.com/api-reference/market-data/get-order-book",
                "https://docs.polymarket.com/api-reference/markets/get-prices-history",
                "https://docs.polymarket.com/api-reference/wss/market",
            ],
            "created_at_utc": now_utc,
            **route,
            **authority_flags(),
        },
    ]


def historical_full_book_acquisition_ledger(now_utc: str) -> list[dict[str, object]]:
    rows = []
    for audit in official_historical_full_book_audit(now_utc):
        rows.append(
            {
                "ledger_row_id": audit["audit_row_id"].replace("audit", "ledger"),
                "venue": audit["venue"],
                "attempted_priority": "VERIFIED_PUBLIC_OFFICIAL_HISTORICAL_FULL_BOOK",
                "acquisition_result": audit["availability_classification"],
                "fetched_historical_full_book_row_count": 0,
                "repo_safe_sample_written": False,
                "exact_gap_or_auth_reason": audit["exact_reason"],
                "substitute_artifact_family": audit["public_substitute_data"],
                "next_route": "CAPTURE_FORWARD_L2_AND_REVIEW_THIRD_PARTY_CANDIDATES",
                "created_at_utc": now_utc,
                **route_defaults("source_evidence"),
                **authority_flags(),
            }
        )
    return rows


def third_party_candidate_rows(now_utc: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, candidate in enumerate(THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATES, start=1):
        rows.append(
            {
                "candidate_source_row_id": f"third_party_historical_full_book_candidate_{index:04d}",
                "venue": candidate["venue"],
                "source_url": candidate["url"],
                "source_id": candidate["source_id"],
                "source_tier": candidate["source_tier"],
                "data_readiness_state": candidate["candidate_state"],
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "exact_reason": candidate["reason"],
                "required_action": "THIRD_PARTY_DATASET_REVIEW",
                "created_at_utc": now_utc,
                **route_defaults("source_evidence"),
                **authority_flags(),
            }
        )
    return rows


def historical_l2_gap_rows(now_utc: str) -> list[dict[str, object]]:
    return [
        {
            "gap_row_id": "kalshi_historical_l2_gap_0001",
            "venue": "kalshi",
            "gap_code": "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
            "gap_detail": "Use DATA1 current REST book snapshots, historical trades/candles, and forward REST polling until public historical L2 source is accepted.",
            "future_pr_route": "future_long_running_full_book_capture_service_PR",
            "owner_action": "CAPTURE_FORWARD_L2",
            "created_at_utc": now_utc,
            **route_defaults("market_data"),
            **authority_flags(),
        },
        {
            "gap_row_id": "polymarket_historical_l2_gap_0001",
            "venue": "polymarket",
            "gap_code": "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
            "gap_detail": "Use DATA1 current CLOB book, public price history/trades, and forward REST polling or WebSocket when dependency is present.",
            "future_pr_route": "future_long_running_full_book_capture_service_PR",
            "owner_action": "CAPTURE_FORWARD_L2",
            "created_at_utc": now_utc,
            **route_defaults("market_data"),
            **authority_flags(),
        },
    ]
