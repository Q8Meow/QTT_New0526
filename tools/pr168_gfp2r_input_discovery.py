#!/usr/bin/env python3
"""Input discovery and DATA1/DATA1A loading for PR168-GFP2R."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from tools.pr168_gfp2r_config import (
    GENERATED_ROOT,
    PR234_MERGE_COMMIT,
    REQUIRED_AGENT_REPORT_IDS,
    REQUIRED_DATA1_REPORT_IDS,
    REQUIRED_DATA1A_REPORT_IDS,
    generated_ref,
    report_path,
)
from tools.pr168_gfp2r_market_implied_probability import opposite_binary_price


KALSHI_SNAPSHOT_JSONL = GENERATED_ROOT / "pr168_data1_snapshots" / "kalshi" / "kalshi_snapshots.jsonl"
POLYMARKET_SNAPSHOT_JSONL = GENERATED_ROOT / "pr168_data1_snapshots" / "polymarket" / "polymarket_snapshots.jsonl"


@dataclass(frozen=True)
class MarketContext:
    context_id: str
    venue: str
    market_id_or_token_id: str
    condition_id: str | None
    ticker: str | None
    title: str
    as_of_utc: str
    snapshot_refs: list[str]
    data1_snapshot_refs: list[str]
    feature_refs: list[str]
    data_quality_ref: str | None
    data_quality_score_non_proof: float
    data_sufficiency_tier: str
    entry_price_yes: float | None
    entry_price_no: float | None
    bid_yes: float | None
    ask_yes: float | None
    bid_no: float | None
    ask_no: float | None
    spread_yes: float | None
    spread_no: float | None
    mid_yes: float | None
    mid_no: float | None
    yes_bid_depth: float
    yes_ask_depth: float
    no_bid_depth: float
    no_ask_depth: float
    top_level_depth: float
    tick_size: float | None
    min_order_size: float | None
    explicit_fee: float | None
    freshness_seconds: float
    price_history: list[float]
    lifecycle_state: str
    resolution_timestamp: str | None
    historical_full_book_required_flag: bool
    historical_full_book_available_flag: bool


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _records(path: Path) -> Any:
    payload = _load_json(path)
    return payload.get("records", payload)


def _report_ref(report_id: str) -> str:
    return generated_ref(report_path(report_id))


def data1a_report_refs() -> list[str]:
    return [_report_ref(report_id) for report_id in REQUIRED_DATA1A_REPORT_IDS if report_path(report_id).exists()]


def data1_report_refs() -> list[str]:
    return [_report_ref(report_id) for report_id in REQUIRED_DATA1_REPORT_IDS if report_path(report_id).exists()]


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _first(rows: list[dict[str, Any]], *, venue: str, data_family: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("venue") == venue and row.get("data_family") == data_family:
            return row
    return None


def _all(rows: list[dict[str, Any]], *, venue: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("venue") == venue]


def _depth(levels: Any) -> float:
    if not isinstance(levels, list):
        return 0.0
    total = 0.0
    for level in levels:
        if isinstance(level, dict):
            total += float(level.get("size", 0.0) or 0.0)
        elif isinstance(level, (list, tuple)) and len(level) > 1:
            total += float(level[1] or 0.0)
    return round(total, 6)


def _top_depth(levels: Any) -> float:
    if not isinstance(levels, list) or not levels:
        return 0.0
    level = levels[0]
    if isinstance(level, dict):
        return float(level.get("size", 0.0) or 0.0)
    if isinstance(level, (list, tuple)) and len(level) > 1:
        return float(level[1] or 0.0)
    return 0.0


def _prices_from_history(row: dict[str, Any] | None) -> list[float]:
    if row is None:
        return []
    normalized = row.get("normalized_record", {})
    prices: list[float] = []
    for item in normalized.get("sample", []) if isinstance(normalized, dict) else []:
        if isinstance(item, dict):
            value = item.get("p") or item.get("close") or item.get("yes_price_dollars")
            if value is not None:
                prices.append(float(value))
    last = normalized.get("last_record") if isinstance(normalized, dict) else None
    if isinstance(last, dict):
        value = last.get("p") or last.get("close") or last.get("yes_price_dollars")
        if value is not None:
            prices.append(float(value))
    return prices


def _seconds_until(as_of: str, timestamp: str | None) -> float:
    if not timestamp:
        return 0.0
    try:
        left = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        right = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    return max(0.0, (right - left).total_seconds())


def _quality_by_venue() -> dict[str, dict[str, Any]]:
    path = report_path("PR168_DATA1A_DataQualityCoverageAudit")
    if not path.exists():
        return {}
    records = _records(path)
    rows = records.get("rows", []) if isinstance(records, dict) else []
    return {str(row.get("venue")): row for row in rows if isinstance(row, dict)}


def _market_context_from_rows(venue: str, rows: list[dict[str, Any]]) -> MarketContext | None:
    metadata = _first(rows, venue=venue, data_family="market_metadata")
    orderbook = _first(rows, venue=venue, data_family="current_full_orderbook_snapshot")
    history = (
        _first(rows, venue=venue, data_family="price_history")
        or _first(rows, venue=venue, data_family="candlestick_history")
        or _first(rows, venue=venue, data_family="trade_history_current")
    )
    if metadata is None or orderbook is None:
        return None
    meta = metadata.get("normalized_record", {})
    book = orderbook.get("normalized_record", {})
    if not isinstance(meta, dict) or not isinstance(book, dict):
        return None
    quality = _quality_by_venue().get(venue, {})
    yes_bid = book.get("best_yes_bid", meta.get("best_bid", meta.get("yes_bid")))
    yes_ask = book.get("best_yes_ask", meta.get("best_ask", meta.get("yes_ask")))
    no_bid = book.get("best_no_bid", meta.get("no_bid"))
    no_ask = book.get("best_no_ask", meta.get("no_ask"))
    if no_bid is None and yes_ask is not None:
        no_bid = opposite_binary_price(float(yes_ask))
    if no_ask is None and yes_bid is not None:
        no_ask = opposite_binary_price(float(yes_bid))
    mid_yes = book.get("mid_yes")
    if mid_yes is None and yes_bid is not None and yes_ask is not None:
        mid_yes = (float(yes_bid) + float(yes_ask)) / 2.0
    mid_no = book.get("mid_no")
    if mid_no is None and no_bid is not None and no_ask is not None:
        mid_no = (float(no_bid) + float(no_ask)) / 2.0
    spread_yes = book.get("spread_yes")
    if spread_yes is None and yes_bid is not None and yes_ask is not None:
        spread_yes = max(0.0, float(yes_ask) - float(yes_bid))
    spread_no = book.get("spread_no")
    if spread_no is None and no_bid is not None and no_ask is not None:
        spread_no = max(0.0, float(no_ask) - float(no_bid))
    yes_bids = book.get("yes_bids", book.get("bids", []))
    asks = book.get("asks", [])
    no_bids = book.get("no_bids", [])
    as_of = str(orderbook.get("as_of_utc") or orderbook.get("qtt_capture_timestamp_utc") or metadata.get("as_of_utc"))
    resolution = meta.get("end_date") or meta.get("close_time") or meta.get("expiration_time")
    feature_refs: list[str] = []
    snapshot_refs: list[str] = []
    for row in _all(rows, venue=venue):
        snapshot_id = row.get("snapshot_row_id")
        if snapshot_id:
            snapshot_refs.append(str(snapshot_id))
        for feature_ref in row.get("feature_refs", []) if isinstance(row.get("feature_refs"), list) else []:
            feature_refs.append(str(feature_ref))
    market_ref = str(
        metadata.get("condition_id")
        or metadata.get("market_id")
        or metadata.get("token_id_or_asset_id")
        or metadata.get("ticker")
    )
    return MarketContext(
        context_id=f"market_context::{venue}::{market_ref}",
        venue=venue,
        market_id_or_token_id=market_ref,
        condition_id=metadata.get("condition_id"),
        ticker=metadata.get("ticker"),
        title=str(meta.get("question") or meta.get("title") or metadata.get("outcome_name") or market_ref),
        as_of_utc=as_of,
        snapshot_refs=snapshot_refs,
        data1_snapshot_refs=[
            generated_ref(KALSHI_SNAPSHOT_JSONL if venue == "kalshi" else POLYMARKET_SNAPSHOT_JSONL)
        ],
        feature_refs=sorted(dict.fromkeys(feature_refs)),
        data_quality_ref=quality.get("data_quality_row_id"),
        data_quality_score_non_proof=float(quality.get("data_quality_score_non_proof", 0.0) or 0.0),
        data_sufficiency_tier=str(quality.get("data_sufficiency_tier", "DATA_SUFFICIENCY_UNKNOWN")),
        entry_price_yes=float(yes_ask) if yes_ask is not None else None,
        entry_price_no=float(no_ask) if no_ask is not None else None,
        bid_yes=float(yes_bid) if yes_bid is not None else None,
        ask_yes=float(yes_ask) if yes_ask is not None else None,
        bid_no=float(no_bid) if no_bid is not None else None,
        ask_no=float(no_ask) if no_ask is not None else None,
        spread_yes=float(spread_yes) if spread_yes is not None else None,
        spread_no=float(spread_no) if spread_no is not None else None,
        mid_yes=float(mid_yes) if mid_yes is not None else None,
        mid_no=float(mid_no) if mid_no is not None else None,
        yes_bid_depth=_depth(yes_bids),
        yes_ask_depth=_depth(asks),
        no_bid_depth=_depth(no_bids),
        no_ask_depth=0.0,
        top_level_depth=max(_top_depth(yes_bids), _top_depth(asks), _top_depth(no_bids), 1.0),
        tick_size=float(book.get("tick_size", meta.get("tick_size"))) if book.get("tick_size", meta.get("tick_size")) is not None else None,
        min_order_size=float(book.get("min_order_size", meta.get("min_order_size"))) if book.get("min_order_size", meta.get("min_order_size")) is not None else None,
        explicit_fee=0.0 if bool(quality.get("fee_coverage_flag")) else None,
        freshness_seconds=float(quality.get("freshness_seconds_max", 0.0) or 0.0),
        price_history=_prices_from_history(history),
        lifecycle_state=str(meta.get("status") or ("active" if meta.get("active") else "unknown")),
        resolution_timestamp=str(resolution) if resolution else None,
        historical_full_book_required_flag=True,
        historical_full_book_available_flag=False,
    )


def load_market_contexts() -> list[MarketContext]:
    rows = [*_jsonl_rows(KALSHI_SNAPSHOT_JSONL), *_jsonl_rows(POLYMARKET_SNAPSHOT_JSONL)]
    contexts = [
        context
        for venue in ("kalshi", "polymarket")
        if (context := _market_context_from_rows(venue, rows)) is not None
    ]
    return sorted(contexts, key=lambda context: (context.venue, context.market_id_or_token_id))


def load_context() -> dict[str, Any]:
    data1a_reports = {report_id: _records(report_path(report_id)) for report_id in REQUIRED_DATA1A_REPORT_IDS if report_path(report_id).exists()}
    data1_reports = {report_id: _records(report_path(report_id)) for report_id in REQUIRED_DATA1_REPORT_IDS if report_path(report_id).exists()}
    agent_reports = {report_id: _records(report_path(report_id)) for report_id in REQUIRED_AGENT_REPORT_IDS if report_path(report_id).exists()}
    return {
        "data1a_reports": data1a_reports,
        "data1_reports": data1_reports,
        "agent_reports": agent_reports,
        "market_contexts": load_market_contexts(),
    }


def discover_inputs(created_at_utc: str) -> dict[str, Any]:
    data1a_missing = [
        _report_ref(report_id) for report_id in REQUIRED_DATA1A_REPORT_IDS if not report_path(report_id).exists()
    ]
    data1_missing = [
        _report_ref(report_id) for report_id in REQUIRED_DATA1_REPORT_IDS if not report_path(report_id).exists()
    ]
    agent_missing = [
        _report_ref(report_id) for report_id in REQUIRED_AGENT_REPORT_IDS if not report_path(report_id).exists()
    ]
    contexts = load_market_contexts()
    return {
        "created_at_utc": created_at_utc,
        "pr234_required_state": "MERGED",
        "pr234_merge_commit_required": PR234_MERGE_COMMIT,
        "DATA1A_required_artifact_count": len(REQUIRED_DATA1A_REPORT_IDS),
        "DATA1A_discovered_artifact_count": len(REQUIRED_DATA1A_REPORT_IDS) - len(data1a_missing),
        "DATA1A_missing_required_artifact_count": len(data1a_missing),
        "DATA1A_missing_required_artifact_refs": data1a_missing,
        "DATA1_required_artifact_count": len(REQUIRED_DATA1_REPORT_IDS),
        "DATA1_discovered_artifact_count": len(REQUIRED_DATA1_REPORT_IDS) - len(data1_missing),
        "DATA1_missing_required_artifact_refs": data1_missing,
        "pr165_d2_agent_crosswalk_missing_refs": agent_missing,
        "market_context_count": len(contexts),
        "market_context_refs": [context.context_id for context in contexts],
        "snapshot_jsonl_refs": [
            generated_ref(KALSHI_SNAPSHOT_JSONL),
            generated_ref(POLYMARKET_SNAPSHOT_JSONL),
        ],
    }


def context_input_values(context: MarketContext, side: str) -> dict[str, Any]:
    side = side.upper()
    entry = context.entry_price_yes if side == "YES" else context.entry_price_no
    mid = context.mid_yes if side == "YES" else context.mid_no
    spread = context.spread_yes if side == "YES" else context.spread_no
    bid_depth = context.yes_bid_depth if side == "YES" else context.no_bid_depth
    ask_depth = context.yes_ask_depth if side == "YES" else context.no_ask_depth
    candidate_cost_stack = max(0.0, float(spread or 0.0) / 2.0) + float(context.explicit_fee or 0.0)
    volatility_proxy = 0.0
    if len(context.price_history) > 1:
        mean = sum(context.price_history) / len(context.price_history)
        variance = sum((price - mean) ** 2 for price in context.price_history) / (len(context.price_history) - 1)
        volatility_proxy = variance ** 0.5
    return {
        "entry_price": entry,
        "payout_value": 1.0,
        "candidate_cost_stack": round(candidate_cost_stack, 6),
        "market_implied_probability": mid,
        "break_even_probability_after_costs": "DERIVED_FROM_ENTRY_PRICE_COST_STACK_AND_PAYOUT",
        "spread": spread,
        "depth": bid_depth + ask_depth,
        "orderbook_levels": True if (bid_depth + ask_depth) > 0 else None,
        "price_band": 0.02,
        "edge_band": 0.02,
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "price_history": context.price_history or None,
        "freshness_seconds": context.freshness_seconds,
        "volatility_proxy": volatility_proxy,
        "order_size_bucket": float(context.min_order_size or 1.0),
        "top_level_depth": context.top_level_depth,
        "explicit_fee": context.explicit_fee,
        "tick_size": context.tick_size,
        "min_order_size": context.min_order_size,
        "snapshot_timestamp": context.as_of_utc,
        "resolution_timestamp": context.resolution_timestamp,
        "resolution_seconds": _seconds_until(context.as_of_utc, context.resolution_timestamp),
        "independent_probability_state": "MISSING_INDEPENDENT_PROBABILITY",
        "p_resolve_yes_candidate": None,
        "candidate_quality_i": context.data_quality_score_non_proof,
        "cost_penalty_i": candidate_cost_stack,
        "constraint_refs": ["no_live_authority", "no_historical_full_book_without_verified_source"],
    }
