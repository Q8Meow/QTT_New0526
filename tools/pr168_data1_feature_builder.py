#!/usr/bin/env python3
"""Build computable non-profit market-data feature rows for DATA1."""

from __future__ import annotations

import math
from statistics import pstdev
from typing import Any

from tools.pr168_data1_config import authority_flags, route_defaults


def build_feature_rows(snapshot_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    features: list[dict[str, object]] = []
    by_snapshot: dict[str, list[str]] = {}
    for snapshot in snapshot_rows:
        normalized = snapshot.get("normalized_record")
        if not isinstance(normalized, dict):
            continue
        feature_values = _features_for_snapshot(snapshot, normalized)
        for name, value in feature_values.items():
            if value is None:
                continue
            feature_id = f"pr168_data1_feature_{len(features) + 1:04d}"
            row = _feature_row(feature_id, snapshot, name, value, now_utc, [])
            features.append(row)
            by_snapshot.setdefault(str(snapshot.get("snapshot_row_id")), []).append(feature_id)
    l2_refs = [str(row["l2_replay_row_id"]) for row in l2_rows]
    for snapshot in snapshot_rows:
        refs = by_snapshot.get(str(snapshot.get("snapshot_row_id")), [])
        snapshot["feature_refs"] = refs
    for l2 in l2_rows:
        l2["feature_refs"] = [feature["feature_row_id"] for feature in features if feature["venue"] == l2["venue"]][:8]
    if l2_refs:
        for feature in features:
            feature["l2_replay_row_refs"] = [ref for ref in l2_refs if ref.startswith(str(feature["venue"]))]
    return features


def _features_for_snapshot(snapshot: dict[str, object], normalized: dict[str, Any]) -> dict[str, object]:
    family = snapshot.get("data_family")
    if family == "current_full_orderbook_snapshot":
        bids = normalized.get("bids") if isinstance(normalized.get("bids"), list) else []
        asks = normalized.get("asks") if isinstance(normalized.get("asks"), list) else []
        yes_bids = normalized.get("yes_bids") if isinstance(normalized.get("yes_bids"), list) else []
        no_bids = normalized.get("no_bids") if isinstance(normalized.get("no_bids"), list) else []
        best_bid = normalized.get("best_yes_bid")
        best_ask = normalized.get("best_yes_ask")
        return {
            "best_yes_bid": best_bid,
            "best_yes_ask": best_ask,
            "best_no_bid": normalized.get("best_no_bid"),
            "best_no_ask": normalized.get("best_no_ask"),
            "mid_yes": normalized.get("mid_yes"),
            "mid_no": normalized.get("mid_no"),
            "spread_yes": normalized.get("spread_yes"),
            "spread_no": normalized.get("spread_no"),
            "top_level_depth_yes": _top_depth(yes_bids or bids, best_bid),
            "top_level_depth_no": _top_depth(no_bids, normalized.get("best_no_bid")),
            "depth_within_1c": _depth_within(yes_bids or bids, best_bid, 0.01),
            "depth_within_2c": _depth_within(yes_bids or bids, best_bid, 0.02),
            "depth_within_5c": _depth_within(yes_bids or bids, best_bid, 0.05),
            "full_book_depth_by_price_level": {"bids": yes_bids or bids, "asks": asks, "no_bids": no_bids},
            "book_imbalance": _imbalance(yes_bids or bids, asks or no_bids),
            "book_slope_proxy": _slope_proxy(yes_bids or bids),
            "price_impact_curve_seed": _impact_curve(yes_bids or bids, asks),
            "fillable_size_at_price_band": _depth_within(yes_bids or bids, best_bid, 0.05),
            "fillable_size_at_edge_band": _depth_within(yes_bids or bids, best_bid, 0.02),
            "orderbook_update_count": 1,
            "orderbook_update_rate": 0.0,
            "last_trade_price": normalized.get("last_trade_price"),
            "tick_size": normalized.get("tick_size"),
            "min_order_size_candidate": normalized.get("min_order_size"),
            "historical_full_book_available_flag": False,
            "historical_full_book_gap_flag": True,
            "forward_l2_capture_available_flag": True,
            "liquidity_score_non_proof": _liquidity_score(best_bid, best_ask, _depth_within(yes_bids or bids, best_bid, 0.05)),
        }
    if "trade" in str(family):
        return {
            "recent_trade_count": normalized.get("record_count"),
            "recent_trade_volume": normalized.get("aggregate_volume"),
            "last_trade_timestamp": normalized.get("last_timestamp"),
        }
    if "price" in str(family) or "candle" in str(family):
        prices = _history_prices(normalized)
        return {
            "price_history_return_15m_if_available": _return(prices, 1),
            "price_history_return_1h": _return(prices, 1),
            "price_history_return_24h": _return(prices, min(24, max(len(prices) - 1, 1))),
            "price_history_volatility_proxy": _volatility(prices),
            "candlestick_open_high_low_close": normalized.get("sample"),
        }
    if str(family) == "market_metadata":
        return {
            "market_lifecycle_state": normalized.get("status") or normalized.get("active"),
            "fee_rate_candidate": normalized.get("fee_rate"),
            "tick_size": normalized.get("tick_size"),
            "min_order_size_candidate": normalized.get("min_order_size"),
        }
    return {}


def _feature_row(
    feature_id: str,
    snapshot: dict[str, object],
    name: str,
    value: object,
    now_utc: str,
    l2_refs: list[str],
) -> dict[str, object]:
    route = route_defaults("market_data")
    return {
        "feature_row_id": feature_id,
        "snapshot_row_refs": [snapshot["snapshot_row_id"]],
        "l2_replay_row_refs": l2_refs,
        "venue": snapshot["venue"],
        "market_id_or_ticker_or_token_id": snapshot.get("ticker") or snapshot.get("token_id_or_asset_id") or snapshot.get("market_id"),
        "feature_family": _family_for_feature(name),
        "feature_name": name,
        "feature_value": value,
        "feature_units": _units_for_feature(name),
        "feature_formula_ref": f"PR168_DATA1_FEATURE_FORMULA::{name}",
        "input_data_authority_class": snapshot.get("data_authority_class"),
        "accepted_truth_flag": False,
        "candidate_only_flag": True,
        "as_of_utc": now_utc,
        "staleness_seconds": 0,
        "missing_input_flags": [],
        "quality_flags": ["PUBLIC_REAL_DATA_CANDIDATE", "NON_PROFIT_MARKET_DATA_FEATURE"],
        "downstream_pr_refs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
        "owning_agent": route["owning_agent"],
        "consumer_agents": route["consumer_agents"],
        "validator_refs": route["validator_refs"],
        "test_refs": route["test_refs"],
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "profit_evidence_created_flag": False,
        "live_authority_created_flag": False,
        **authority_flags(),
    }


def _family_for_feature(name: str) -> str:
    if "spread" in name or "bid" in name or "ask" in name or "depth" in name or "book" in name:
        return "orderbook_microstructure"
    if "trade" in name:
        return "trade_history"
    if "price_history" in name or "volatility" in name or "candle" in name:
        return "price_history"
    return "market_metadata"


def _units_for_feature(name: str) -> str:
    if "depth" in name or "size" in name or "volume" in name or "count" in name:
        return "contracts_or_rows"
    if "rate" in name:
        return "updates_per_second"
    if "flag" in name:
        return "boolean"
    if "state" in name:
        return "categorical"
    return "dollars_per_contract_or_unitless"


def _top_depth(levels: list[dict[str, float]], best_price: object) -> float | None:
    if best_price is None:
        return None
    for level in levels:
        if math.isclose(float(level["price"]), float(best_price), abs_tol=1e-9):
            return float(level["size"])
    return None


def _depth_within(levels: list[dict[str, float]], best_price: object, band: float) -> float | None:
    if best_price is None:
        return None
    best = float(best_price)
    return round(sum(float(level["size"]) for level in levels if best - band <= float(level["price"]) <= best + band), 8)


def _imbalance(left: list[dict[str, float]], right: list[dict[str, float]]) -> float | None:
    left_depth = sum(float(row["size"]) for row in left)
    right_depth = sum(float(row["size"]) for row in right)
    total = left_depth + right_depth
    if total <= 0:
        return None
    return round((left_depth - right_depth) / total, 8)


def _slope_proxy(levels: list[dict[str, float]]) -> float | None:
    if len(levels) < 2:
        return None
    price_span = abs(float(levels[-1]["price"]) - float(levels[0]["price"]))
    depth_span = abs(float(levels[-1]["size"]) - float(levels[0]["size"]))
    return round(depth_span / price_span, 8) if price_span else None


def _impact_curve(bids: list[dict[str, float]], asks: list[dict[str, float]]) -> dict[str, object]:
    return {
        "bid_cumulative_depth_top_5": _cumulative(bids[-5:]),
        "ask_cumulative_depth_top_5": _cumulative(asks[:5]),
    }


def _cumulative(levels: list[dict[str, float]]) -> float:
    return round(sum(float(row["size"]) for row in levels), 8)


def _liquidity_score(best_bid: object, best_ask: object, depth: float | None) -> float | None:
    if best_bid is None or best_ask is None or depth is None:
        return None
    spread = max(float(best_ask) - float(best_bid), 0.0001)
    return round(float(depth) / spread, 8)


def _history_prices(normalized: dict[str, object]) -> list[float]:
    prices: list[float] = []
    sample = normalized.get("sample")
    if not isinstance(sample, list):
        return prices
    for row in sample:
        if not isinstance(row, dict):
            continue
        value = row.get("p") or row.get("price") or row.get("close")
        if value is None and isinstance(row.get("yes_ask"), dict):
            value = row["yes_ask"].get("close")
        try:
            if value is not None:
                prices.append(float(value))
        except (TypeError, ValueError):
            pass
    return prices


def _return(prices: list[float], lag: int) -> float | None:
    if len(prices) <= lag or prices[-lag - 1] == 0:
        return None
    return round((prices[-1] - prices[-lag - 1]) / prices[-lag - 1], 8)


def _volatility(prices: list[float]) -> float | None:
    if len(prices) < 2:
        return None
    returns = [(prices[index] - prices[index - 1]) for index in range(1, len(prices))]
    return round(pstdev(returns), 8) if len(returns) >= 2 else abs(round(returns[0], 8))
