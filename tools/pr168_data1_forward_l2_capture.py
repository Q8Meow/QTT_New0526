#!/usr/bin/env python3
"""Forward full-book replay bootstrap rows from public REST snapshots."""

from __future__ import annotations

from tools.pr168_data1_config import authority_flags, route_defaults


def build_forward_l2_rows(snapshot_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for snapshot in snapshot_rows:
        if snapshot.get("data_family") != "current_full_orderbook_snapshot":
            continue
        normalized = snapshot.get("normalized_record")
        if not isinstance(normalized, dict):
            continue
        venue = str(snapshot["venue"])
        row_id = f"{venue}_forward_l2_rest_poll_0001"
        rows.append(
            {
                "l2_replay_row_id": row_id,
                "venue": venue,
                "capture_session_id": f"pr168_data1_{venue}_rest_poll_bootstrap",
                "capture_mode": "REST_POLL",
                "market_id_or_ticker_or_condition_id": snapshot.get("ticker")
                or snapshot.get("condition_id")
                or snapshot.get("market_id"),
                "token_id_or_asset_id": snapshot.get("token_id_or_asset_id"),
                "sequence_number_if_available": None,
                "venue_timestamp": snapshot.get("venue_timestamp"),
                "qtt_capture_timestamp_utc": now_utc,
                "event_type": "book_snapshot",
                "bids": normalized.get("bids") or [],
                "asks": normalized.get("asks") or [],
                "yes_bids": normalized.get("yes_bids") or [],
                "no_bids": normalized.get("no_bids") or [],
                "price_level_changes": [],
                "last_trade_price": normalized.get("last_trade_price"),
                "best_bid": normalized.get("best_yes_bid"),
                "best_ask": normalized.get("best_yes_ask"),
                "spread": normalized.get("spread_yes"),
                "book_hash_or_venue_raw_hash": normalized.get("venue_raw_book_hash"),
                "venue_raw_hash_authority_flag": False,
                "reconstruction_flag": False,
                "reconstruction_method_ref": None,
                "source_url": snapshot.get("source_url"),
                "endpoint_or_ws_channel": snapshot.get("endpoint_name"),
                "accepted_truth_flag": False,
                "candidate_only_flag": True,
                "feature_refs": [],
                **route_defaults("market_data"),
                **authority_flags(),
            }
        )
    return rows
