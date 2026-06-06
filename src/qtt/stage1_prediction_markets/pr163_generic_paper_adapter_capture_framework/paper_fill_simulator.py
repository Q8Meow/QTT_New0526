"""Deterministic paper fill simulator with bounded orderbook depth walking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .paper_scenario_grid import Scenario


@dataclass(frozen=True)
class FillSimulation:
    filled_qty: float
    residual_qty: float
    vwap_fill_price: float
    gross_fill_notional: float
    level_fills: tuple[dict[str, Any], ...]
    maker_taker: str
    terminal_state: str
    reason_code: str
    selected_snapshot_ref: str
    arrival_mid: float
    depth_walk_level_count: int


def synthetic_depth(snapshot: dict[str, Any], scenario: Scenario) -> dict[str, list[dict[str, float]]]:
    if scenario.name == "NO_LIQUIDITY_REST_OR_REJECT_WITH_REASON":
        return {"asks": [], "bids": []}
    best_ask = float(snapshot["best_ask"])
    best_bid = float(snapshot["best_bid"])
    ask_top = float(snapshot.get("ask_top_size", 0))
    bid_top = float(snapshot.get("bid_top_size", 0))
    ask_depth = max(float(snapshot.get("ask_depth", ask_top)), ask_top)
    bid_depth = max(float(snapshot.get("bid_depth", bid_top)), bid_top)
    ask_mid = max((ask_depth - ask_top) / 2.0, 0.0)
    bid_mid = max((bid_depth - bid_top) / 2.0, 0.0)
    return {
        "asks": [
            {"price": round(min(best_ask, 0.99), 4), "size": ask_top},
            {"price": round(min(best_ask + 0.01, 0.99), 4), "size": ask_mid},
            {"price": round(min(best_ask + 0.02, 0.99), 4), "size": max(ask_depth - ask_top - ask_mid, 0.0)},
        ],
        "bids": [
            {"price": round(max(best_bid, 0.01), 4), "size": bid_top},
            {"price": round(max(best_bid - 0.01, 0.01), 4), "size": bid_mid},
            {"price": round(max(best_bid - 0.02, 0.01), 4), "size": max(bid_depth - bid_top - bid_mid, 0.0)},
        ],
    }


def price_for_scenario(snapshot: dict[str, Any], scenario: Scenario) -> float:
    best_ask = float(snapshot["best_ask"])
    best_bid = float(snapshot["best_bid"])
    if scenario.price_mode == "BUY_MARKETABLE_FULL":
        return round(min(best_ask + 0.03, 0.99), 4)
    if scenario.price_mode == "SELL_MARKETABLE_FULL":
        return round(max(best_bid - 0.03, 0.01), 4)
    if scenario.price_mode == "BUY_RESTING":
        return round(max(best_bid, 0.01), 4)
    if scenario.price_mode == "SELL_RESTING":
        return round(min(best_ask, 0.99), 4)
    if scenario.price_mode == "BUY_TOP_ONLY":
        return round(best_ask, 4)
    if scenario.price_mode == "SELL_TOP_ONLY":
        return round(best_bid, 4)
    if scenario.price_mode == "INVALID_TICK":
        return 0.4555
    if scenario.price_mode == "INVALID_DOMAIN":
        return 1.25
    if scenario.price_mode == "NO_LIQUIDITY":
        return round(min(best_ask + 0.02, 0.99), 4)
    return round(best_ask, 4)


def walk_orderbook(side: str, limit_price: float, requested_qty: float, depth: dict[str, list[dict[str, float]]]) -> FillSimulation:
    remaining = float(requested_qty)
    gross = 0.0
    level_fills: list[dict[str, Any]] = []
    levels = depth["asks"] if side.startswith("BUY") else depth["bids"]
    if side.startswith("BUY"):
        eligible = sorted((level for level in levels if level["price"] <= limit_price), key=lambda row: row["price"])
    else:
        eligible = sorted((level for level in levels if level["price"] >= limit_price), key=lambda row: row["price"], reverse=True)
    for level in eligible:
        if remaining <= 0:
            break
        fill_qty = min(remaining, float(level["size"]))
        if fill_qty <= 0:
            continue
        gross += fill_qty * float(level["price"])
        remaining -= fill_qty
        level_fills.append(
            {
                "level_price": round(float(level["price"]), 6),
                "available_level_size": round(float(level["size"]), 6),
                "fill_qty_at_level": round(fill_qty, 6),
            }
        )
    filled = float(requested_qty) - remaining
    vwap = gross / filled if filled > 0 else 0.0
    return FillSimulation(
        filled_qty=round(filled, 6),
        residual_qty=round(max(remaining, 0.0), 6),
        vwap_fill_price=round(vwap, 6),
        gross_fill_notional=round(gross, 6),
        level_fills=tuple(level_fills),
        maker_taker="TAKER" if filled > 0 else "MAKER_OR_RESTING",
        terminal_state="",
        reason_code="",
        selected_snapshot_ref="",
        arrival_mid=0.0,
        depth_walk_level_count=len(level_fills),
    )


def simulate_fill(
    *,
    scenario: Scenario,
    side: str,
    limit_price: float,
    requested_qty: float,
    snapshot: dict[str, Any],
    selected_snapshot_ref: str,
    pretrade_status: str,
) -> FillSimulation:
    arrival_mid = round((float(snapshot["best_bid"]) + float(snapshot["best_ask"])) / 2.0, 6)
    if pretrade_status != "PAPER_PRETRADE_PASS":
        return FillSimulation(
            filled_qty=0.0,
            residual_qty=float(requested_qty),
            vwap_fill_price=0.0,
            gross_fill_notional=0.0,
            level_fills=(),
            maker_taker="NONE",
            terminal_state="PRETRADE_REJECTED",
            reason_code=f"{scenario.name}_PRETRADE_REJECTED",
            selected_snapshot_ref=selected_snapshot_ref,
            arrival_mid=arrival_mid,
            depth_walk_level_count=0,
        )
    depth = synthetic_depth(snapshot, scenario)
    walked = walk_orderbook(side, limit_price, requested_qty, depth)
    filled = walked.filled_qty
    residual = walked.residual_qty
    terminal_state = "RESTING"
    reason = "PAPER_ORDER_RESTING_NO_SYNTHETIC_FILL"
    if scenario.post_only and filled > 0:
        filled = 0.0
        residual = float(requested_qty)
        terminal_state = "REJECTED"
        reason = "PAPER_POST_ONLY_MARKETABLE_REJECTED"
        level_fills: tuple[dict[str, Any], ...] = ()
        gross = 0.0
        vwap = 0.0
    elif scenario.order_type == "FOK" and residual > 0:
        filled = 0.0
        residual = float(requested_qty)
        terminal_state = "REJECTED"
        reason = "PAPER_FOK_KILL_NO_FILL"
        level_fills = ()
        gross = 0.0
        vwap = 0.0
    elif filled == 0 and scenario.name == "NO_LIQUIDITY_REST_OR_REJECT_WITH_REASON":
        terminal_state = "REJECTED"
        reason = "PAPER_NO_LIQUIDITY_REJECT_WITH_EXACT_REASON"
        level_fills = ()
        gross = 0.0
        vwap = 0.0
    else:
        level_fills = walked.level_fills
        gross = walked.gross_fill_notional
        vwap = walked.vwap_fill_price
        if filled >= requested_qty:
            terminal_state = "FILLED"
            reason = "PAPER_SYNTHETIC_FULL_FILL"
        elif filled > 0 and scenario.order_type == "FAK":
            terminal_state = "CANCELLED"
            reason = "PAPER_FAK_PARTIAL_FILL_CANCEL_RESIDUAL"
        elif filled > 0:
            terminal_state = "RESTING"
            reason = "PAPER_PARTIAL_FILL_RESIDUAL_RESTING"
        elif scenario.order_type == "GTD":
            terminal_state = "EXPIRED"
            reason = "PAPER_GTD_EXPIRED_NO_FILL"
        elif scenario.name == "GTC_REST_THEN_CANCEL":
            terminal_state = "CANCELLED"
            reason = "PAPER_GTC_REST_THEN_CANCEL"
    return FillSimulation(
        filled_qty=round(filled, 6),
        residual_qty=round(residual, 6),
        vwap_fill_price=round(vwap, 6),
        gross_fill_notional=round(gross, 6),
        level_fills=level_fills,
        maker_taker="TAKER" if filled > 0 else "MAKER_OR_RESTING",
        terminal_state=terminal_state,
        reason_code=reason,
        selected_snapshot_ref=selected_snapshot_ref,
        arrival_mid=arrival_mid,
        depth_walk_level_count=len(level_fills),
    )
