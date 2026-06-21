#!/usr/bin/env python3
"""Normalize public Kalshi and Polymarket payloads into DATA1 snapshot rows."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from typing import Any

from tools.pr168_data1_config import (
    KALSHI_BASE_URL,
    POLYMARKET_CLOB_BASE_URL,
    POLYMARKET_DATA_BASE_URL,
    POLYMARKET_GAMMA_BASE_URL,
    authority_flags,
    route_defaults,
)
from tools.pr168_data1_http_client import HttpResult


def normalize_snapshot_rows(
    kalshi_data: dict[str, object],
    polymarket_data: dict[str, object],
    now_utc: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(_kalshi_rows(kalshi_data, now_utc))
    rows.extend(_polymarket_rows(polymarket_data, now_utc))
    return rows


def _kalshi_rows(data: dict[str, object], now_utc: str) -> list[dict[str, object]]:
    selected = data.get("selected_market") if isinstance(data.get("selected_market"), dict) else {}
    results = data.get("results") if isinstance(data.get("results"), dict) else {}
    assert isinstance(results, dict)
    rows: list[dict[str, object]] = []
    ticker = str(selected.get("ticker") or "")
    event_ticker = str(selected.get("event_ticker") or selected.get("event_id") or "")
    series_ticker = str(selected.get("series_ticker") or (ticker.split("-")[0] if ticker else ""))
    markets_result = _result(results.get("markets"))
    rows.append(
        _snapshot_row(
            row_id="kalshi_market_metadata_0001",
            venue="kalshi",
            data_family="market_metadata",
            market_id=ticker,
            event_id=event_ticker,
            series_id=series_ticker,
            ticker=ticker,
            condition_id=None,
            token_id=None,
            outcome_name=str(selected.get("title") or selected.get("yes_sub_title") or "selected_market"),
            side="market",
            as_of_utc=now_utc,
            source_url=markets_result.url if markets_result else f"{KALSHI_BASE_URL}/markets",
            endpoint_name="kalshi_markets",
            request_params={"limit": 100, "status": "open"},
            http_status=markets_result.status if markets_result else None,
            data_status=markets_result.data_status if markets_result else "ENDPOINT_UNAVAILABLE",
            source_tier="OFFICIAL_PUBLIC_API",
            historical_full_book_state="HISTORICAL_FULL_BOOK_UNAVAILABLE",
            forward_l2_capture_state="FORWARD_L2_REST_POLL_CAPTURED",
            data_authority_class="DATA_READY_PUBLIC_REAL_SNAPSHOT_CANDIDATE",
            raw_record=_compact_market(selected),
            normalized_record={
                "status": selected.get("status"),
                "title": selected.get("title"),
                "yes_bid": _to_float(selected.get("yes_bid_dollars")),
                "yes_ask": _to_float(selected.get("yes_ask_dollars")),
                "no_bid": _to_float(selected.get("no_bid_dollars")),
                "no_ask": _to_float(selected.get("no_ask_dollars")),
                "liquidity_dollars": _to_float(selected.get("liquidity_dollars")),
                "volume": _to_float(selected.get("volume_fp") or selected.get("volume")),
                "close_time": selected.get("close_time"),
                "expiration_time": selected.get("expiration_time"),
            },
            price_unit="dollars_per_contract",
            quantity_unit="contracts",
            venue_timestamp=selected.get("last_update_time") or selected.get("close_time"),
        )
    )
    orderbook_result = _first_result(results, "orderbook_")
    if orderbook_result:
        book = _kalshi_book(orderbook_result.json_value)
        rows.append(
            _snapshot_row(
                row_id="kalshi_orderbook_snapshot_0001",
                venue="kalshi",
                data_family="current_full_orderbook_snapshot",
                market_id=ticker,
                event_id=event_ticker,
                series_id=series_ticker,
                ticker=ticker,
                condition_id=None,
                token_id=None,
                outcome_name="binary_market",
                side="yes_no",
                as_of_utc=now_utc,
                source_url=orderbook_result.url,
                endpoint_name="kalshi_current_orderbook",
                request_params={"ticker": ticker},
                http_status=orderbook_result.status,
                data_status=orderbook_result.data_status,
                source_tier="OFFICIAL_PUBLIC_API",
                historical_full_book_state="HISTORICAL_FULL_BOOK_UNAVAILABLE",
                forward_l2_capture_state="FORWARD_L2_REST_POLL_CAPTURED",
                data_authority_class="DATA_READY_PUBLIC_REAL_ORDERBOOK_CANDIDATE",
                raw_record={
                    "yes_level_count": len(book["yes_bids"]),
                    "no_level_count": len(book["no_bids"]),
                },
                normalized_record=book,
                price_unit="dollars_per_contract",
                quantity_unit="contracts",
                venue_timestamp=now_utc,
            )
        )
    for result_key, row_id, data_family, endpoint in [
        ("market_trades", "kalshi_market_trades_0001", "trade_history_current", "kalshi_live_trades"),
        ("historical_trades", "kalshi_historical_trades_0001", "historical_trade_history", "kalshi_historical_trades"),
        ("candlesticks", "kalshi_candlesticks_0001", "candlestick_history", "kalshi_market_candlesticks"),
        ("historical_cutoff", "kalshi_historical_cutoff_0001", "historical_cutoff", "kalshi_historical_cutoff"),
    ]:
        result = _result(results.get(result_key))
        if result:
            rows.append(
                _history_row(
                    row_id=row_id,
                    venue="kalshi",
                    data_family=data_family,
                    market_id=ticker,
                    event_id=event_ticker,
                    series_id=series_ticker,
                    ticker=ticker,
                    condition_id=None,
                    token_id=None,
                    now_utc=now_utc,
                    result=result,
                    endpoint_name=endpoint,
                    normalized_record=_compact_history(result.json_value),
                )
            )
    return rows


def _polymarket_rows(data: dict[str, object], now_utc: str) -> list[dict[str, object]]:
    selected = data.get("selected_market") if isinstance(data.get("selected_market"), dict) else {}
    selected_token = str(data.get("selected_token") or "")
    results = data.get("results") if isinstance(data.get("results"), dict) else {}
    assert isinstance(results, dict)
    rows: list[dict[str, object]] = []
    market_id = str(selected.get("id") or selected.get("market") or "")
    condition_id = str(selected.get("conditionId") or "")
    outcomes = _parse_array(selected.get("outcomes"))
    token_ids = [str(token) for token in _parse_array(selected.get("clobTokenIds"))]
    outcome_name = str(outcomes[0]) if outcomes else "outcome_0"
    markets_result = _result(results.get("markets"))
    rows.append(
        _snapshot_row(
            row_id="polymarket_market_metadata_0001",
            venue="polymarket",
            data_family="market_metadata",
            market_id=market_id,
            event_id=str(selected.get("eventId") or selected.get("event_id") or ""),
            series_id=str(selected.get("category") or ""),
            ticker=None,
            condition_id=condition_id,
            token_id=selected_token,
            outcome_name=outcome_name,
            side="market",
            as_of_utc=now_utc,
            source_url=markets_result.url if markets_result else f"{POLYMARKET_GAMMA_BASE_URL}/markets",
            endpoint_name="polymarket_gamma_markets",
            request_params={"active": "true", "closed": "false", "limit": 25},
            http_status=markets_result.status if markets_result else None,
            data_status=markets_result.data_status if markets_result else "ENDPOINT_UNAVAILABLE",
            source_tier="OFFICIAL_PUBLIC_API",
            historical_full_book_state="HISTORICAL_FULL_BOOK_UNAVAILABLE",
            forward_l2_capture_state="FORWARD_L2_REST_POLL_CAPTURED",
            data_authority_class="DATA_READY_PUBLIC_REAL_SNAPSHOT_CANDIDATE",
            raw_record=_compact_market(selected),
            normalized_record={
                "question": selected.get("question"),
                "outcomes": outcomes,
                "clob_token_ids": token_ids,
                "active": selected.get("active"),
                "closed": selected.get("closed"),
                "liquidity": _to_float(selected.get("liquidity")),
                "volume": _to_float(selected.get("volume")),
                "volume_24h": _to_float(selected.get("volume24hr")),
                "best_bid": _to_float(selected.get("bestBid")),
                "best_ask": _to_float(selected.get("bestAsk")),
                "spread": _to_float(selected.get("spread")),
                "last_trade_price": _to_float(selected.get("lastTradePrice")),
                "min_order_size": _to_float(selected.get("orderMinSize")),
                "tick_size": _to_float(selected.get("orderPriceMinTickSize")),
                "end_date": selected.get("endDate"),
            },
            price_unit="dollars_per_contract",
            quantity_unit="contracts",
            venue_timestamp=selected.get("updatedAt") or selected.get("endDate"),
        )
    )
    book_result = _result(results.get("book"))
    if book_result:
        book = _polymarket_book(book_result.json_value)
        rows.append(
            _snapshot_row(
                row_id="polymarket_orderbook_snapshot_0001",
                venue="polymarket",
                data_family="current_full_orderbook_snapshot",
                market_id=market_id,
                event_id=str(selected.get("eventId") or ""),
                series_id=str(selected.get("category") or ""),
                ticker=None,
                condition_id=condition_id,
                token_id=selected_token,
                outcome_name=outcome_name,
                side="outcome_token",
                as_of_utc=now_utc,
                source_url=book_result.url,
                endpoint_name="polymarket_clob_book",
                request_params={"token_id": selected_token},
                http_status=book_result.status,
                data_status=book_result.data_status,
                source_tier="OFFICIAL_PUBLIC_API",
                historical_full_book_state="HISTORICAL_FULL_BOOK_UNAVAILABLE",
                forward_l2_capture_state="FORWARD_L2_REST_POLL_CAPTURED",
                data_authority_class="DATA_READY_PUBLIC_REAL_ORDERBOOK_CANDIDATE",
                raw_record={
                    "bid_level_count": len(book["bids"]),
                    "ask_level_count": len(book["asks"]),
                    "venue_raw_book_hash": book.get("venue_raw_book_hash"),
                },
                normalized_record=book,
                price_unit="dollars_per_contract",
                quantity_unit="contracts",
                venue_timestamp=book.get("venue_timestamp"),
            )
        )
    for result_key, row_id, data_family, endpoint, source_url in [
        ("prices_history", "polymarket_price_history_0001", "price_history", "polymarket_prices_history", f"{POLYMARKET_CLOB_BASE_URL}/prices-history"),
        ("data_trades", "polymarket_data_trades_0001", "trade_history", "polymarket_data_trades", f"{POLYMARKET_DATA_BASE_URL}/trades"),
    ]:
        result = _result(results.get(result_key))
        if result:
            rows.append(
                _history_row(
                    row_id=row_id,
                    venue="polymarket",
                    data_family=data_family,
                    market_id=market_id,
                    event_id=str(selected.get("eventId") or ""),
                    series_id=str(selected.get("category") or ""),
                    ticker=None,
                    condition_id=condition_id,
                    token_id=selected_token,
                    now_utc=now_utc,
                    result=result,
                    endpoint_name=endpoint,
                    normalized_record=_compact_history(result.json_value),
                    source_url_fallback=source_url,
                )
            )
    return rows


def _snapshot_row(
    *,
    row_id: str,
    venue: str,
    data_family: str,
    market_id: str,
    event_id: str,
    series_id: str,
    ticker: str | None,
    condition_id: str | None,
    token_id: str | None,
    outcome_name: str,
    side: str,
    as_of_utc: str,
    source_url: str,
    endpoint_name: str,
    request_params: dict[str, object],
    http_status: int | None,
    data_status: str,
    source_tier: str,
    historical_full_book_state: str,
    forward_l2_capture_state: str,
    data_authority_class: str,
    raw_record: dict[str, object],
    normalized_record: dict[str, object],
    price_unit: str,
    quantity_unit: str,
    venue_timestamp: object,
) -> dict[str, object]:
    route = route_defaults("market_data")
    return {
        "snapshot_row_id": row_id,
        "venue": venue,
        "data_family": data_family,
        "market_id": market_id,
        "event_id": event_id,
        "series_id": series_id,
        "ticker": ticker,
        "condition_id": condition_id,
        "token_id_or_asset_id": token_id,
        "outcome_name": outcome_name,
        "side": side,
        "as_of_utc": as_of_utc,
        "source_url": source_url,
        "endpoint_name": endpoint_name,
        "request_params": request_params,
        "http_status": http_status,
        "data_status": data_status,
        "source_tier": source_tier,
        "historical_full_book_state": historical_full_book_state,
        "forward_l2_capture_state": forward_l2_capture_state,
        "data_authority_class": data_authority_class,
        "accepted_truth_flag": False,
        "candidate_only_flag": True,
        "schema_inferred_fields": sorted(normalized_record),
        "raw_record_ref_or_inline_compact_record": raw_record,
        "normalized_record": normalized_record,
        "unit_normalization": {
            "price_formula": "venue dollar price used directly when present; Kalshi yes ask inferred as 1 - no bid only for binary market symmetry",
            "quantity_formula": "venue quantity used as contract count or fixed-point count when venue provides fp field",
        },
        "price_unit": price_unit,
        "quantity_unit": quantity_unit,
        "venue_timestamp": venue_timestamp,
        "qtt_capture_timestamp_utc": as_of_utc,
        "ttl_or_revalidation_due_utc": None,
        "feature_refs": [],
        **route,
        **authority_flags(),
    }


def _history_row(
    *,
    row_id: str,
    venue: str,
    data_family: str,
    market_id: str,
    event_id: str,
    series_id: str,
    ticker: str | None,
    condition_id: str | None,
    token_id: str | None,
    now_utc: str,
    result: HttpResult,
    endpoint_name: str,
    normalized_record: dict[str, object],
    source_url_fallback: str | None = None,
) -> dict[str, object]:
    status_class = (
        "DATA_READY_PUBLIC_REAL_PRICE_HISTORY_CANDIDATE"
        if "price" in data_family or "candle" in data_family
        else "DATA_READY_PUBLIC_REAL_TRADE_HISTORY_CANDIDATE"
        if "trade" in data_family
        else "DATA_READY_PUBLIC_REAL_HISTORY_CANDIDATE"
    )
    return _snapshot_row(
        row_id=row_id,
        venue=venue,
        data_family=data_family,
        market_id=market_id,
        event_id=event_id,
        series_id=series_id,
        ticker=ticker,
        condition_id=condition_id,
        token_id=token_id,
        outcome_name="history",
        side="history",
        as_of_utc=now_utc,
        source_url=result.url or source_url_fallback or "",
        endpoint_name=endpoint_name,
        request_params={},
        http_status=result.status,
        data_status=result.data_status,
        source_tier="OFFICIAL_PUBLIC_API",
        historical_full_book_state="HISTORICAL_FULL_BOOK_UNAVAILABLE",
        forward_l2_capture_state="NOT_APPLICABLE",
        data_authority_class=status_class,
        raw_record={"status": result.status, "error": result.error, "url": result.url},
        normalized_record=normalized_record,
        price_unit="dollars_per_contract",
        quantity_unit="contracts",
        venue_timestamp=normalized_record.get("last_timestamp") or now_utc,
    )


def _kalshi_book(value: object) -> dict[str, object]:
    source = value if isinstance(value, dict) else {}
    book = source.get("orderbook_fp") if isinstance(source.get("orderbook_fp"), dict) else source.get("orderbook")
    book = book if isinstance(book, dict) else {}
    yes_bids = _levels(book.get("yes_dollars") or book.get("yes") or [])
    no_bids = _levels(book.get("no_dollars") or book.get("no") or [])
    best_yes_bid = _best_bid(yes_bids)
    best_no_bid = _best_bid(no_bids)
    yes_ask = _one_minus(best_no_bid)
    no_ask = _one_minus(best_yes_bid)
    return {
        "yes_bids": yes_bids,
        "no_bids": no_bids,
        "bids": yes_bids,
        "asks": [],
        "best_yes_bid": best_yes_bid,
        "best_yes_ask": yes_ask,
        "best_no_bid": best_no_bid,
        "best_no_ask": no_ask,
        "mid_yes": _mid(best_yes_bid, yes_ask),
        "mid_no": _mid(best_no_bid, no_ask),
        "spread_yes": _spread(best_yes_bid, yes_ask),
        "spread_no": _spread(best_no_bid, no_ask),
        "binary_ask_derivation_flags": {
            "yes_ask_from_no_bid": best_no_bid is not None,
            "no_ask_from_yes_bid": best_yes_bid is not None,
        },
    }


def _polymarket_book(value: object) -> dict[str, object]:
    source = value if isinstance(value, dict) else {}
    bids = sorted(_dict_levels(source.get("bids") or []), key=lambda row: row["price"])
    asks = sorted(_dict_levels(source.get("asks") or []), key=lambda row: row["price"])
    best_bid = max((row["price"] for row in bids), default=None)
    best_ask = min((row["price"] for row in asks), default=None)
    return {
        "bids": bids,
        "asks": asks,
        "yes_bids": bids,
        "no_bids": [],
        "best_yes_bid": best_bid,
        "best_yes_ask": best_ask,
        "best_no_bid": None,
        "best_no_ask": None,
        "mid_yes": _mid(best_bid, best_ask),
        "spread_yes": _spread(best_bid, best_ask),
        "last_trade_price": _to_float(source.get("last_trade_price")),
        "min_order_size": _to_float(source.get("min_order_size")),
        "tick_size": _to_float(source.get("tick_size")),
        "venue_timestamp": source.get("timestamp"),
        "venue_raw_book_hash": source.get("hash"),
        "venue_raw_hash_authority_flag": False,
    }


def _levels(value: object) -> list[dict[str, float]]:
    levels: list[dict[str, float]] = []
    if not isinstance(value, list):
        return levels
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            price = _to_float(item[0])
            size = _to_float(item[1])
            if price is not None and size is not None:
                levels.append({"price": price, "size": size})
    return sorted(levels, key=lambda row: row["price"])


def _dict_levels(value: object) -> list[dict[str, float]]:
    levels: list[dict[str, float]] = []
    if not isinstance(value, list):
        return levels
    for item in value:
        if not isinstance(item, dict):
            continue
        price = _to_float(item.get("price"))
        size = _to_float(item.get("size"))
        if price is not None and size is not None:
            levels.append({"price": price, "size": size})
    return levels


def _compact_history(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        rows = []
        for key in ("trades", "history", "candlesticks", "candles"):
            if isinstance(value.get(key), list):
                rows = value[key]
                break
        if rows:
            last = rows[-1] if isinstance(rows[-1], dict) else {}
            volume = sum(_to_float(row.get("count_fp") or row.get("size") or row.get("volume") or 0) or 0 for row in rows if isinstance(row, dict))
            return {
                "record_count": len(rows),
                "sample": [_sanitize_inline_sample(row) for row in rows[:3]],
                "last_record": _sanitize_inline_sample(last),
                "last_timestamp": last.get("t") or last.get("created_time") or last.get("period_interval_end_ts"),
                "aggregate_volume": round(volume, 8),
            }
        return {"record_count": len(value), "sample": _sanitize_inline_sample(dict(list(value.items())[:8]))}
    if isinstance(value, list):
        return {"record_count": len(value), "sample": [_sanitize_inline_sample(row) for row in value[:3]]}
    return {"record_count": 0, "sample": value}


def _compact_market(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    keep = [
        "ticker",
        "event_ticker",
        "id",
        "conditionId",
        "question",
        "title",
        "status",
        "active",
        "closed",
        "liquidity",
        "liquidity_dollars",
        "volume",
        "volume_fp",
        "bestBid",
        "bestAsk",
        "yes_bid_dollars",
        "yes_ask_dollars",
        "no_bid_dollars",
        "no_ask_dollars",
        "clobTokenIds",
        "outcomes",
    ]
    return _sanitize_inline_sample({key: value.get(key) for key in keep if key in value})


def _sanitize_inline_sample(value: object) -> object:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if item in ("", None) and ("image" in lowered or "path" in lowered or "url" in lowered):
                continue
            sanitized[key] = _sanitize_inline_sample(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_inline_sample(item) for item in value]
    return value


def _result(value: object) -> HttpResult | None:
    return value if isinstance(value, HttpResult) else None


def _first_result(results: dict[str, object], prefix: str) -> HttpResult | None:
    for key, value in results.items():
        if key.startswith(prefix) and isinstance(value, HttpResult) and value.ok:
            return value
    for key, value in results.items():
        if key.startswith(prefix) and isinstance(value, HttpResult):
            return value
    return None


def _parse_array(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def _best_bid(levels: list[dict[str, float]]) -> float | None:
    return max((row["price"] for row in levels), default=None)


def _one_minus(value: float | None) -> float | None:
    return round(1.0 - value, 8) if value is not None else None


def _mid(bid: float | None, ask: float | None) -> float | None:
    return round((bid + ask) / 2.0, 8) if bid is not None and ask is not None else None


def _spread(bid: float | None, ask: float | None) -> float | None:
    return round(ask - bid, 8) if bid is not None and ask is not None else None
