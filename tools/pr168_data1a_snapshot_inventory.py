#!/usr/bin/env python3
"""DATA1 snapshot inventory and owner question A counts."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tools.pr168_data1a_config import (
    KALSHI_FORWARD_L2_JSONL,
    KALSHI_SNAPSHOT_JSONL,
    POLYMARKET_FORWARD_L2_JSONL,
    POLYMARKET_SNAPSHOT_JSONL,
    count_confidence,
    generated_ref,
    route_defaults,
)


def _market_key(row: dict[str, Any]) -> str | None:
    if row.get("venue") == "kalshi":
        return row.get("ticker") or row.get("market_id")
    if row.get("venue") == "polymarket":
        return row.get("condition_id") or row.get("market_id")
    return row.get("market_id") or row.get("ticker")


def _token_keys(row: dict[str, Any]) -> set[str]:
    keys = {str(row.get("token_id_or_asset_id")) for row in [row] if row.get("token_id_or_asset_id")}
    normalized = row.get("normalized_record") or {}
    if isinstance(normalized, dict):
        for token in normalized.get("clob_token_ids", []) or []:
            if token:
                keys.add(str(token))
    return keys


def _price_levels(row: dict[str, Any]) -> int:
    normalized = row.get("normalized_record") or row
    if row.get("venue") == "polymarket":
        return len(normalized.get("bids") or []) + len(normalized.get("asks") or [])
    if row.get("venue") == "kalshi":
        return len(normalized.get("yes_bids") or []) + len(normalized.get("no_bids") or [])
    return sum(len(normalized.get(key) or []) for key in ("bids", "asks", "yes_bids", "no_bids"))


def _record_count(row: dict[str, Any]) -> int:
    normalized = row.get("normalized_record") or {}
    value = normalized.get("record_count")
    if isinstance(value, int):
        return value
    sample = normalized.get("sample")
    if isinstance(sample, list):
        return len(sample)
    return 0


def build_fetch_inventory(context: dict[str, Any], created_at_utc: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = list(context["kalshi_rows"]) + list(context["polymarket_rows"])
    l2_rows = list(context["kalshi_l2_rows"]) + list(context["polymarket_l2_rows"])
    inventory_rows: list[dict[str, Any]] = []

    def add_inventory_row(
        *,
        venue: str,
        data_family: str,
        source_file: str,
        source_row_id: str,
        market_key: str | None,
        event_key: str | None,
        series_key: str | None,
        condition_key: str | None,
        token_key: str | None,
        endpoint_name: str,
        count_family: str,
        contribution: int,
        source_url: str | None,
    ) -> None:
        inventory_rows.append(
            {
                "inventory_row_id": f"inventory_{len(inventory_rows) + 1:05d}",
                "venue": venue,
                "data_family": data_family,
                "source_file": source_file,
                "source_row_id": source_row_id,
                "market_key": market_key,
                "event_key": event_key,
                "series_key": series_key,
                "condition_key": condition_key,
                "token_key": token_key,
                "endpoint_name": endpoint_name,
                "count_family": count_family,
                "count_contribution": contribution,
                "as_of_utc": created_at_utc,
                "source_url": source_url,
                **route_defaults("market_data", data1_refs=[source_file], upstream_refs=[source_row_id]),
            }
        )

    source_by_venue = {
        "kalshi": generated_ref(KALSHI_SNAPSHOT_JSONL),
        "polymarket": generated_ref(POLYMARKET_SNAPSHOT_JSONL),
    }
    l2_source_by_venue = {
        "kalshi": generated_ref(KALSHI_FORWARD_L2_JSONL),
        "polymarket": generated_ref(POLYMARKET_FORWARD_L2_JSONL),
    }
    for row in rows:
        source_file = source_by_venue[str(row["venue"])]
        source_row_id = str(row.get("snapshot_row_id"))
        family = str(row.get("data_family"))
        contribution = _record_count(row) or 1
        if family == "current_full_orderbook_snapshot":
            contribution = 1
            add_inventory_row(
                venue=str(row["venue"]),
                data_family=family,
                source_file=source_file,
                source_row_id=source_row_id,
                market_key=_market_key(row),
                event_key=row.get("event_id"),
                series_key=row.get("series_id"),
                condition_key=row.get("condition_id"),
                token_key=row.get("token_id_or_asset_id"),
                endpoint_name=str(row.get("endpoint_name")),
                count_family="orderbook_snapshot_record",
                contribution=1,
                source_url=row.get("source_url"),
            )
            add_inventory_row(
                venue=str(row["venue"]),
                data_family=family,
                source_file=source_file,
                source_row_id=source_row_id,
                market_key=_market_key(row),
                event_key=row.get("event_id"),
                series_key=row.get("series_id"),
                condition_key=row.get("condition_id"),
                token_key=row.get("token_id_or_asset_id"),
                endpoint_name=str(row.get("endpoint_name")),
                count_family="orderbook_price_level",
                contribution=_price_levels(row),
                source_url=row.get("source_url"),
            )
        else:
            add_inventory_row(
                venue=str(row["venue"]),
                data_family=family,
                source_file=source_file,
                source_row_id=source_row_id,
                market_key=_market_key(row),
                event_key=row.get("event_id"),
                series_key=row.get("series_id"),
                condition_key=row.get("condition_id"),
                token_key=row.get("token_id_or_asset_id"),
                endpoint_name=str(row.get("endpoint_name")),
                count_family=family,
                contribution=contribution,
                source_url=row.get("source_url"),
            )
    for row in l2_rows:
        source_file = l2_source_by_venue[str(row["venue"])]
        add_inventory_row(
            venue=str(row["venue"]),
            data_family="forward_l2",
            source_file=source_file,
            source_row_id=str(row.get("l2_replay_row_id")),
            market_key=row.get("market_id_or_ticker_or_condition_id"),
            event_key=None,
            series_key=None,
            condition_key=row.get("market_id_or_ticker_or_condition_id") if row.get("venue") == "polymarket" else None,
            token_key=row.get("token_id_or_asset_id"),
            endpoint_name=str(row.get("endpoint_or_ws_channel")),
            count_family="forward_l2_row",
            contribution=1,
            source_url=row.get("source_url"),
        )

    by_venue = {venue: [row for row in rows if row.get("venue") == venue] for venue in ("kalshi", "polymarket")}
    by_venue_l2 = {venue: [row for row in l2_rows if row.get("venue") == venue] for venue in ("kalshi", "polymarket")}
    metrics: dict[str, int | float] = {}
    for venue, venue_rows in by_venue.items():
        orderbook_rows = [row for row in venue_rows if row.get("data_family") == "current_full_orderbook_snapshot"]
        metrics[f"{venue}_unique_market_count"] = len({_market_key(row) for row in venue_rows if _market_key(row)})
        metrics[f"{venue}_orderbook_market_count"] = len({_market_key(row) for row in orderbook_rows if _market_key(row)})
        metrics[f"{venue}_orderbook_snapshot_row_count"] = len(orderbook_rows)
        metrics[f"{venue}_orderbook_price_level_count"] = sum(_price_levels(row) for row in orderbook_rows)
        metrics[f"{venue}_snapshot_total_row_count"] = len(venue_rows)
        metrics[f"{venue}_forward_l2_row_count"] = len(by_venue_l2[venue])
    metrics["kalshi_unique_event_count"] = len({row.get("event_id") for row in by_venue["kalshi"] if row.get("event_id")})
    metrics["kalshi_unique_series_count"] = len({row.get("series_id") for row in by_venue["kalshi"] if row.get("series_id")})
    metrics["kalshi_historical_trade_row_count"] = sum(
        _record_count(row) for row in by_venue["kalshi"] if row.get("data_family") == "historical_trade_history"
    )
    metrics["kalshi_recent_trade_row_count"] = sum(
        _record_count(row) for row in by_venue["kalshi"] if row.get("data_family") == "trade_history_current"
    )
    metrics["kalshi_candlestick_point_count"] = sum(
        _record_count(row) for row in by_venue["kalshi"] if row.get("data_family") == "candlestick_history"
    )
    metrics["polymarket_unique_event_count"] = len({row.get("event_id") for row in by_venue["polymarket"] if row.get("event_id")})
    metrics["polymarket_unique_condition_count"] = len(
        {row.get("condition_id") for row in by_venue["polymarket"] if row.get("condition_id")}
    )
    token_keys: set[str] = set()
    for row in by_venue["polymarket"]:
        token_keys.update(_token_keys(row))
    metrics["polymarket_unique_token_or_asset_count"] = len(token_keys)
    metrics["polymarket_price_history_point_count"] = sum(
        _record_count(row) for row in by_venue["polymarket"] if row.get("data_family") == "price_history"
    )
    metrics["polymarket_trade_or_activity_row_count"] = sum(
        _record_count(row) for row in by_venue["polymarket"] if row.get("data_family") == "trade_history"
    )
    metrics["total_snapshot_jsonl_file_count"] = 2
    metrics["total_manifest_file_count"] = len(context["manifests"])
    metrics["total_snapshot_row_count"] = len(rows)
    metrics["total_forward_l2_row_count"] = len(l2_rows)
    metrics["total_orderbook_snapshot_row_count"] = metrics["kalshi_orderbook_snapshot_row_count"] + metrics["polymarket_orderbook_snapshot_row_count"]
    metrics["total_orderbook_price_level_count"] = metrics["kalshi_orderbook_price_level_count"] + metrics["polymarket_orderbook_price_level_count"]
    metrics["total_historical_trade_row_count"] = metrics["kalshi_historical_trade_row_count"] + metrics["polymarket_trade_or_activity_row_count"]
    metrics["total_price_history_or_candle_point_count"] = metrics["kalshi_candlestick_point_count"] + metrics["polymarket_price_history_point_count"]
    features = context["reports"].get("PR168_DATA1_NormalizedMarketDataFeatureRegistry", {}).get("records", [])
    metrics["total_feature_row_count"] = len(features) if isinstance(features, list) else 0

    source_refs = [generated_ref(KALSHI_SNAPSHOT_JSONL), generated_ref(POLYMARKET_SNAPSHOT_JSONL), generated_ref(KALSHI_FORWARD_L2_JSONL), generated_ref(POLYMARKET_FORWARD_L2_JSONL)]
    count_rows = [
        count_confidence(
            name,
            int(value),
            "EXACT_FROM_JSONL_ROW_SCAN",
            source_file_refs=source_refs,
            row_selection_rule=f"deterministic DATA1A scan for {name}",
            dedupe_key_used="venue_specific_market_identity" if "market_count" in name else "source_row_id",
            nested_array_expansion_rule="price/history/trade arrays expanded from normalized_record.record_count when applicable",
        )
        for name, value in sorted(metrics.items())
    ]
    count_rows.append(
        count_confidence(
            "qku_pre_data1_exact_baseline_count",
            None,
            "UNKNOWN_BASELINE_MISSING_UPSTREAM_REF",
            source_file_refs=["docs/master_plan/generated/PR168_GFP_QKUComputationCoverage.report.json"],
            row_selection_rule="no exact pre-DATA1 missing-market-data baseline artifact found",
            missing_or_unknown_reason="PR168_GFP rows expose numeric-input-missing status, not a clean DATA1-pre/post market-data block baseline",
            confidence_level="UNKNOWN",
            gfp2r_allowed=False,
        )
    )
    metrics["inventory_count_family_counts"] = dict(Counter(row["count_family"] for row in inventory_rows))
    return metrics, inventory_rows, count_rows
