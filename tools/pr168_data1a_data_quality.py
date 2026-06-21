#!/usr/bin/env python3
"""DATA1A freshness, quality, coverage, sufficiency, and severity scoring."""

from __future__ import annotations

from statistics import median
from typing import Any

from tools.pr168_data1a_config import generated_ref, parse_iso, report_path, route_defaults


REQUIRED_SNAPSHOT_FIELDS = [
    "snapshot_row_id",
    "venue",
    "data_family",
    "as_of_utc",
    "source_url",
    "endpoint_name",
    "data_status",
    "normalized_record",
    "downstream_pr_refs",
    "owning_agent",
    "consumer_agents",
    "validator_refs",
    "test_refs",
    "no_orphan_status",
]

EDGE_PATHWAYS = [
    "execution_adjusted_edge",
    "fill_adjusted_expected_pnl",
    "TCA",
    "LCB",
    "capacity",
    "FDR",
    "portfolio_utility",
    "scenario_ladder",
    "calibration",
    "no_trade_margin",
]


def _market_key(row: dict[str, Any]) -> str:
    if row.get("venue") == "kalshi":
        return str(row.get("ticker") or row.get("market_id"))
    return str(row.get("condition_id") or row.get("market_id") or row.get("token_id_or_asset_id"))


def _feature_names_by_market(context: dict[str, Any]) -> dict[str, set[str]]:
    features = context["reports"].get("PR168_DATA1_NormalizedMarketDataFeatureRegistry", {}).get("records", [])
    names: dict[str, set[str]] = {}
    if not isinstance(features, list):
        return names
    for feature in features:
        market = str(feature.get("market_id_or_ticker_or_token_id"))
        names.setdefault(market, set()).add(str(feature.get("feature_name")))
    return names


def _freshness_seconds(row: dict[str, Any], audit_time: str) -> int:
    audit_dt = parse_iso(audit_time)
    asof_dt = parse_iso(row.get("as_of_utc")) or parse_iso(row.get("qtt_capture_timestamp_utc"))
    if not audit_dt or not asof_dt:
        return 0
    return max(0, int((audit_dt - asof_dt).total_seconds()))


def _score_bool(value: bool) -> float:
    return 1.0 if value else 0.0


def build_data_quality(context: dict[str, Any], inventory: dict[str, Any], created_at_utc: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = list(context["kalshi_rows"]) + list(context["polymarket_rows"])
    l2_rows = list(context["kalshi_l2_rows"]) + list(context["polymarket_l2_rows"])
    features_by_market = _feature_names_by_market(context)
    markets = sorted({_market_key(row) for row in rows if _market_key(row)})
    quality_rows: list[dict[str, Any]] = []
    severity_rows: list[dict[str, Any]] = []
    freshness_values = [_freshness_seconds(row, created_at_utc) for row in rows]

    for index, market in enumerate(markets, start=1):
        market_rows = [row for row in rows if _market_key(row) == market or str(row.get("token_id_or_asset_id")) == market]
        venue = str(market_rows[0].get("venue")) if market_rows else "unknown"
        names = set()
        for row in market_rows:
            names.update(features_by_market.get(str(row.get("ticker") or row.get("token_id_or_asset_id") or row.get("market_id")), set()))
            names.update(features_by_market.get(market, set()))
        has_orderbook = any(row.get("data_family") == "current_full_orderbook_snapshot" for row in market_rows)
        has_spread = "spread_yes" in names or any((row.get("normalized_record") or {}).get("spread_yes") is not None for row in market_rows)
        has_depth = bool({"full_book_depth_by_price_level", "top_level_depth_no", "top_level_depth_yes"} & names)
        has_depth_1c = "depth_within_1c" in names
        has_depth_2c = "depth_within_2c" in names
        has_depth_5c = "depth_within_5c" in names
        has_trade = any(row.get("data_family") in {"trade_history", "trade_history_current", "historical_trade_history"} for row in market_rows)
        has_price_history = any(row.get("data_family") in {"price_history", "candlestick_history"} for row in market_rows)
        has_lifecycle = any(row.get("data_family") == "market_metadata" for row in market_rows)
        has_fee = "tick_size" in names or "min_order_size_candidate" in names
        has_tick = "tick_size" in names
        has_min_order = "min_order_size_candidate" in names
        has_forward_l2 = any(str(l2.get("market_id_or_ticker_or_condition_id")) == market or str(l2.get("token_id_or_asset_id")) == market for l2 in l2_rows)
        missing_fields = [
            f"{row.get('snapshot_row_id')}::{field}"
            for row in market_rows
            for field in REQUIRED_SNAPSHOT_FIELDS
            if field not in row or row.get(field) in (None, "")
        ]
        schema_completeness = 1.0 - (len(missing_fields) / max(1, len(market_rows) * len(REQUIRED_SNAPSHOT_FIELDS)))
        freshness_score = 1.0 if max((_freshness_seconds(row, created_at_utc) for row in market_rows), default=0) <= 86400 else 0.5
        trade_or_price_score = 1.0 if has_trade and has_price_history else 0.5 if has_trade or has_price_history else 0.0
        fee_score = 1.0 if has_fee else 0.0
        source_score = 1.0 if all(row.get("source_url") and row.get("endpoint_name") for row in market_rows) else 0.0
        downstream_score = 1.0 if has_orderbook and (has_trade or has_price_history) else 0.5 if has_orderbook else 0.0
        quality_score = round(
            0.18 * freshness_score
            + 0.16 * schema_completeness
            + 0.14 * _score_bool(has_spread)
            + 0.14 * _score_bool(has_depth)
            + 0.10 * trade_or_price_score
            + 0.08 * _score_bool(has_lifecycle)
            + 0.08 * fee_score
            + 0.06 * source_score
            + 0.06 * downstream_score,
            6,
        )
        if has_orderbook and has_spread and has_depth and (has_trade or has_price_history) and has_lifecycle and has_fee:
            tier = "DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE"
            severity = "GREEN_READY_FOR_CANDIDATE_COMPUTE"
            route = "RUN_RP2_REPLAY_PAPER"
        elif has_orderbook and has_depth and (has_trade or has_price_history):
            tier = "DATA_SUFFICIENCY_TIER_B_FORMULA_COMPUTE_READY_CANDIDATE"
            severity = "YELLOW_READY_WITH_FORMULA_BINDING_REPAIR"
            route = "RUN_GFP2R_CANDIDATE_COMPUTE"
        elif has_orderbook:
            tier = "DATA_SUFFICIENCY_TIER_C_RESEARCH_ONLY_CANDIDATE"
            severity = "ORANGE_PARTIAL_DATA_QUALITY_LIMITATION"
            route = "FORMULA_INPUT_BINDING_REPAIR"
        else:
            tier = "DATA_SUFFICIENCY_TIER_D_GAP_ROUTED"
            severity = "RED_BLOCKED_MISSING_CRITICAL_DATA_FAMILY"
            route = "DATA1B_FETCH_MORE_PUBLIC_DATA"
        quality_row = {
            "data_quality_row_id": f"data_quality_{index:05d}",
            "venue": venue,
            "market_or_token_ref": market,
            "snapshot_refs": [row.get("snapshot_row_id") for row in market_rows],
            "feature_names": sorted(names),
            "freshness_seconds_max": max((_freshness_seconds(row, created_at_utc) for row in market_rows), default=0),
            "missing_required_fields": missing_fields,
            "schema_completeness_score": round(schema_completeness, 6),
            "spread_coverage_flag": has_spread,
            "depth_coverage_flag": has_depth,
            "depth_within_1c_coverage_flag": has_depth_1c,
            "depth_within_2c_coverage_flag": has_depth_2c,
            "depth_within_5c_coverage_flag": has_depth_5c,
            "trade_coverage_flag": has_trade,
            "price_history_coverage_flag": has_price_history,
            "resolution_lifecycle_coverage_flag": has_lifecycle,
            "fee_coverage_flag": has_fee,
            "tick_size_coverage_flag": has_tick,
            "min_order_size_coverage_flag": has_min_order,
            "forward_l2_coverage_flag": has_forward_l2,
            "historical_full_book_coverage_flag": False,
            "data_quality_score_non_proof": quality_score,
            "data_sufficiency_tier": tier,
            "sufficiency_reason_codes": [
                "current_orderbook_present" if has_orderbook else "current_orderbook_missing",
                "spread_present" if has_spread else "spread_missing_or_derived_only",
                "depth_present" if has_depth else "depth_missing",
                "history_present" if (has_trade or has_price_history) else "history_missing",
                "historical_full_book_missing",
            ],
            "GFP2R_candidate_compute_ready_flag": tier in {
                "DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE",
                "DATA_SUFFICIENCY_TIER_B_FORMULA_COMPUTE_READY_CANDIDATE",
            },
            "RP2_replay_paper_ready_flag": tier == "DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE",
            "RANK2_evidence_ranking_ready_flag": tier in {
                "DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE",
                "DATA_SUFFICIENCY_TIER_B_FORMULA_COMPUTE_READY_CANDIDATE",
            },
            "damaged_metric_pathways_if_gap": [
                pathway
                for pathway in EDGE_PATHWAYS
                if (pathway in {"TCA", "fill_adjusted_expected_pnl", "capacity"} and not has_depth)
                or (pathway in {"calibration", "LCB"} and not (has_trade or has_price_history))
                or (pathway == "execution_adjusted_edge" and not has_spread)
                or (pathway == "no_trade_margin" and not has_orderbook)
            ],
            "created_at_utc": created_at_utc,
            **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_DataQualityFreshnessCoverageAudit"))]),
        }
        quality_rows.append(quality_row)
        severity_rows.append(
            {
                "severity_action_row_id": f"data_quality_action_{index:05d}",
                "venue": venue,
                "market_or_token_ref": market,
                "severity_state": severity,
                "route_family": route,
                "next_action": route,
                "quality_gap_codes": quality_row["sufficiency_reason_codes"],
                "damaged_metric_pathways": quality_row["damaged_metric_pathways_if_gap"],
                "expected_downstream_unblock_count": 3 if tier.startswith("DATA_SUFFICIENCY_TIER_A") else 2,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=[generated_ref(report_path("PR168_DATA1_DataQualityFreshnessCoverageAudit"))]),
            }
        )

    def rate(key: str) -> float:
        return round(sum(1 for row in quality_rows if row[key]) / max(1, len(quality_rows)), 6)

    freshness_bucket_counts = {
        "lte_1h": sum(1 for value in freshness_values if value <= 3600),
        "lte_24h": sum(1 for value in freshness_values if 3600 < value <= 86400),
        "gt_24h": sum(1 for value in freshness_values if value > 86400),
    }
    summary = {
        "data_freshness_min_seconds": min(freshness_values or [0]),
        "data_freshness_median_seconds": int(median(freshness_values or [0])),
        "data_freshness_max_seconds": max(freshness_values or [0]),
        "freshness_bucket_counts": freshness_bucket_counts,
        "missing_required_field_count": sum(len(row["missing_required_fields"]) for row in quality_rows),
        "missing_required_field_rate": round(
            sum(len(row["missing_required_fields"]) for row in quality_rows)
            / max(1, len(rows) * len(REQUIRED_SNAPSHOT_FIELDS)),
            6,
        ),
        "schema_completeness_score": round(
            sum(row["schema_completeness_score"] for row in quality_rows) / max(1, len(quality_rows)),
            6,
        ),
        "asof_timestamp_coverage_rate": round(sum(1 for row in rows if row.get("as_of_utc")) / max(1, len(rows)), 6),
        "source_url_coverage_rate": round(sum(1 for row in rows if row.get("source_url")) / max(1, len(rows)), 6),
        "endpoint_name_coverage_rate": round(sum(1 for row in rows if row.get("endpoint_name")) / max(1, len(rows)), 6),
        "unit_normalization_coverage_rate": round(sum(1 for row in rows if row.get("unit_normalization")) / max(1, len(rows)), 6),
        "spread_coverage_market_count": sum(1 for row in quality_rows if row["spread_coverage_flag"]),
        "spread_coverage_rate": rate("spread_coverage_flag"),
        "depth_coverage_market_count": sum(1 for row in quality_rows if row["depth_coverage_flag"]),
        "depth_coverage_rate": rate("depth_coverage_flag"),
        "depth_within_1c_coverage_rate": rate("depth_within_1c_coverage_flag"),
        "depth_within_2c_coverage_rate": rate("depth_within_2c_coverage_flag"),
        "depth_within_5c_coverage_rate": rate("depth_within_5c_coverage_flag"),
        "trade_coverage_market_count": sum(1 for row in quality_rows if row["trade_coverage_flag"]),
        "trade_coverage_rate": rate("trade_coverage_flag"),
        "price_history_coverage_market_count": sum(1 for row in quality_rows if row["price_history_coverage_flag"]),
        "price_history_coverage_rate": rate("price_history_coverage_flag"),
        "resolution_lifecycle_coverage_market_count": sum(1 for row in quality_rows if row["resolution_lifecycle_coverage_flag"]),
        "resolution_lifecycle_coverage_rate": rate("resolution_lifecycle_coverage_flag"),
        "fee_coverage_market_count": sum(1 for row in quality_rows if row["fee_coverage_flag"]),
        "fee_coverage_rate": rate("fee_coverage_flag"),
        "tick_size_coverage_market_count": sum(1 for row in quality_rows if row["tick_size_coverage_flag"]),
        "tick_size_coverage_rate": rate("tick_size_coverage_flag"),
        "min_order_size_coverage_market_count": sum(1 for row in quality_rows if row["min_order_size_coverage_flag"]),
        "min_order_size_coverage_rate": rate("min_order_size_coverage_flag"),
        "forward_l2_coverage_market_count": sum(1 for row in quality_rows if row["forward_l2_coverage_flag"]),
        "forward_l2_coverage_rate": rate("forward_l2_coverage_flag"),
        "historical_full_book_coverage_market_count": 0,
        "historical_full_book_coverage_rate": 0.0,
        "data_quality_score_median_non_proof": round(median([row["data_quality_score_non_proof"] for row in quality_rows] or [0.0]), 6),
        "data_quality_green_count": sum(1 for row in severity_rows if str(row["severity_state"]).startswith("GREEN")),
        "data_quality_yellow_count": sum(1 for row in severity_rows if str(row["severity_state"]).startswith("YELLOW")),
        "data_quality_orange_count": sum(1 for row in severity_rows if str(row["severity_state"]).startswith("ORANGE")),
        "data_quality_red_count": sum(1 for row in severity_rows if str(row["severity_state"]).startswith("RED")),
        **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_DataQualityFreshnessCoverageAudit"))]),
    }
    return summary, quality_rows, severity_rows
