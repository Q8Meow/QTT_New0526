"""Normalize PR162A repo-local non-live candidate datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from . import constants as c


NORMALIZED_FIELDS = (
    "timestamp",
    "market_id_or_ticker_or_token_or_contract_candidate",
    "venue_scope",
    "event_category",
    "outcome_side",
    "price_candidate",
    "bid_candidate",
    "ask_candidate",
    "spread_candidate",
    "midpoint_candidate",
    "last_trade_price_candidate",
    "volume_candidate",
    "liquidity_candidate",
    "open_interest_candidate",
    "settlement_status_candidate",
    "resolution_candidate",
    "source_event_id_candidate",
    "source_market_id_candidate",
    "data_quality_flags",
    "missing_value_flags",
    "missing_value_reasons",
    "candidate_authority_class",
    "source_class",
    "access_rights_status",
    "qku_mapping_refs",
    "scenario_mapping_refs",
    "pr161f_run_plan_refs",
    "pr162_adapter_refs",
    "quantum_feature_refs",
)


def normalize_kalshi_raw(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    payload = raw_payload["raw_payload"]
    ticker = payload["ticker"]
    rows: list[dict[str, Any]] = []
    for trade in payload.get("trades") or []:
        rows.append(
            _record(
                row_id=f"PR162A-NORMALIZED-KALSHI-TRADE-{trade['trade_id']}",
                timestamp=_iso_z(trade["created_time"]),
                ticker=ticker,
                outcome_side=trade.get("taker_outcome_side"),
                price=_decimal_or_none(trade.get("yes_price_dollars")),
                last_trade_price=_decimal_or_none(trade.get("yes_price_dollars")),
                volume=_decimal_or_none(trade.get("count_fp")),
                open_interest=None,
                bid=None,
                ask=None,
                source_event_id=payload.get("market", {}).get("event_ticker"),
                data_quality_flags=["TRADE_RECORD_NO_ORDERBOOK_DEPTH"],
                missing_reasons={
                    "bid_candidate": "not_provided_by_public_historical_trade_record",
                    "ask_candidate": "not_provided_by_public_historical_trade_record",
                    "open_interest_candidate": "not_provided_by_public_historical_trade_record",
                    "liquidity_candidate": "not_provided_by_public_historical_trade_record",
                    "settlement_status_candidate": "post_settlement_market_metadata_excluded_from_pre_resolution_features",
                    "resolution_candidate": "post_settlement_market_metadata_excluded_from_pre_resolution_features",
                },
            )
        )
    for candle in payload.get("candlesticks") or []:
        bid = _decimal_or_none((candle.get("yes_bid") or {}).get("close"))
        ask = _decimal_or_none((candle.get("yes_ask") or {}).get("close"))
        price = _decimal_or_none((candle.get("price") or {}).get("close"))
        rows.append(
            _record(
                row_id=f"PR162A-NORMALIZED-KALSHI-CANDLE-{ticker}-{candle['end_period_ts']}",
                timestamp=datetime.fromtimestamp(
                    int(candle["end_period_ts"]),
                    tz=timezone.utc,
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                ticker=ticker,
                outcome_side="yes",
                price=price,
                last_trade_price=None,
                volume=_decimal_or_none(candle.get("volume")),
                open_interest=_decimal_or_none(candle.get("open_interest")),
                bid=bid,
                ask=ask,
                source_event_id=payload.get("market", {}).get("event_ticker"),
                data_quality_flags=["CANDLESTICK_RECORD_PRE_RESOLUTION_FEATURE_ONLY"],
                missing_reasons={
                    "last_trade_price_candidate": "not_provided_by_public_historical_candlestick_record",
                    "liquidity_candidate": "not_provided_by_public_historical_candlestick_record",
                    "settlement_status_candidate": "post_settlement_market_metadata_excluded_from_pre_resolution_features",
                    "resolution_candidate": "post_settlement_market_metadata_excluded_from_pre_resolution_features",
                },
            )
        )
    return sorted(rows, key=lambda row: (row["timestamp"], row["record_id"]))


def _record(
    *,
    row_id: str,
    timestamp: str,
    ticker: str,
    outcome_side: str | None,
    price: float | None,
    last_trade_price: float | None,
    volume: float | None,
    open_interest: float | None,
    bid: float | None,
    ask: float | None,
    source_event_id: str | None,
    data_quality_flags: list[str],
    missing_reasons: dict[str, str],
) -> dict[str, Any]:
    midpoint = None
    spread = None
    if bid is not None and ask is not None:
        midpoint = round((bid + ask) / 2, 6)
        spread = round(ask - bid, 6)
    row = {
        "record_id": row_id,
        "created_by_pr": c.PR_ID,
        "timestamp": timestamp,
        "market_id_or_ticker_or_token_or_contract_candidate": ticker,
        "venue_scope": "KALSHI",
        "event_category": "SPORTS_MULTIGAME_EVENT_CONTRACT_CANDIDATE",
        "outcome_side": outcome_side,
        "price_candidate": price,
        "bid_candidate": bid,
        "ask_candidate": ask,
        "spread_candidate": spread,
        "midpoint_candidate": midpoint,
        "last_trade_price_candidate": last_trade_price,
        "volume_candidate": volume,
        "liquidity_candidate": None,
        "open_interest_candidate": open_interest,
        "settlement_status_candidate": None,
        "resolution_candidate": None,
        "source_event_id_candidate": source_event_id,
        "source_market_id_candidate": ticker,
        "data_quality_flags": data_quality_flags,
        "missing_value_reasons": dict(sorted(missing_reasons.items())),
        "candidate_authority_class": "REPO_LOCAL_OFFICIAL_PUBLIC_HISTORICAL_DATASET_CANDIDATE",
        "source_class": "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE",
        "access_rights_status": "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
        "qku_mapping_refs": ["PR162A_QKU_SCOPE_EXPLICIT_KALSHI_COMPATIBLE_ONLY"],
        "scenario_mapping_refs": [
            "PR162A_SCENARIO_SCOPE_OBSERVED_TWO_ROW_KALSHI_WINDOW_ONLY"
        ],
        "pr161f_run_plan_refs": [],
        "dataset_seed_candidate_flag": True,
        "adapter_mechanics_fixture_flag": True,
        "dataset_coverage_state": c.DATASET_SEED_CANDIDATE_READY,
        "pr162_adapter_refs": [
            "PR162_ReplayDataAdapterContract.report.json",
            "PR162_PaperDataAdapterContract.report.json",
        ],
        "quantum_feature_refs": [
            "binary_outcome_price_series",
            "yes_no_spread_series",
            "liquidity_depth_proxy_series",
        ],
    }
    row["missing_value_flags"] = sorted(missing_reasons)
    return row


def _decimal_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(Decimal(str(value)))


def _iso_z(value: str) -> str:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
