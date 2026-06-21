#!/usr/bin/env python3
"""Historical full-book truth ledger for PR168-DATA1A."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


def build_historical_full_book_truth(
    context: dict[str, Any],
    inventory: dict[str, Any],
    qku_rows: list[dict[str, Any]],
    created_at_utc: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    availability = context["reports"].get("PR168_DATA1_HistoricalFullBookAvailabilityAudit", {}).get("records", [])
    acquisition = context["reports"].get("PR168_DATA1_HistoricalFullBookAcquisitionLedger", {}).get("records", [])
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(availability if isinstance(availability, list) else [], start=1):
        classification = "HISTORICAL_FULL_BOOK_PUBLIC_UNAVAILABLE"
        if "AUTH" in str(row.get("availability_classification", "")):
            classification = "HISTORICAL_FULL_BOOK_AUTH_REQUIRED"
        rows.append(
            {
                "historical_full_book_row_id": f"historical_full_book_{index:05d}",
                "venue": row.get("venue"),
                "classification_state": classification,
                "DATA1_availability_ref": row.get("audit_row_id"),
                "source_urls": row.get("source_urls"),
                "verified_public_rows_count": 0,
                "verified_public_market_count": 0,
                "forward_l2_substitute_row_count": inventory.get(f"{row.get('venue')}_forward_l2_row_count", 0),
                "substitute_allowed_flag": True,
                "substitute_data_families": [
                    "current_book",
                    "forward_l2",
                    "historical_trade",
                    "candle",
                    "price_history",
                    "lifecycle",
                    "resolution",
                ],
                "substitute_limitations": "Substitutes are not historical full-book replay and cannot prove pre-capture book states.",
                "formula_bias_risk_reason": "Full-depth queue, adverse selection, and historical liquidity regimes are unobserved before DATA1 capture start.",
                "replay_bias_risk_reason": "Replay/paper must use trade/candle/price-history/current-book proxies and record bias.",
                "required_future_acquisition_route": "DATA1B_HISTORICAL_L2_ACQUISITION_REVIEW",
                "GFP2R_historical_full_book_assumption_allowed_flag": False,
                "created_at_utc": created_at_utc,
                **route_defaults("source_evidence", data1_refs=[generated_ref(report_path("PR168_DATA1_HistoricalFullBookAvailabilityAudit"))]),
            }
        )
    for offset, qku in enumerate(qku_rows[:5], start=len(rows) + 1):
        rows.append(
            {
                "historical_full_book_row_id": f"historical_full_book_{offset:05d}",
                "venue": "multi_venue",
                "classification_state": "HISTORICAL_PRICE_TRADE_CANDLE_SUBSTITUTE_ONLY",
                "DATA1_availability_ref": qku.get("qku_unblock_row_id"),
                "source_urls": [],
                "verified_public_rows_count": 0,
                "verified_public_market_count": 0,
                "forward_l2_substitute_row_count": inventory.get("total_forward_l2_row_count", 0),
                "substitute_allowed_flag": True,
                "substitute_data_families": [
                    "current_book",
                    "forward_l2",
                    "historical_trade",
                    "candle",
                    "price_history",
                    "lifecycle",
                    "resolution",
                ],
                "substitute_limitations": "Candidate-only formula route; no historical full-book assumption allowed.",
                "formula_bias_risk_reason": qku.get("historical_full_book_gap_route"),
                "replay_bias_risk_reason": "Queue/fill replay is proxy-only until historical L2 acquisition.",
                "required_future_acquisition_route": "DATA1B_HISTORICAL_L2_ACQUISITION_REVIEW",
                "GFP2R_historical_full_book_assumption_allowed_flag": False,
                "qku_id_if_available": qku.get("qku_id"),
                "formula_id_if_available": qku.get("formula_id_if_available"),
                "created_at_utc": created_at_utc,
                **route_defaults("source_evidence", data1_refs=[generated_ref(report_path("PR168_DATA1_HistoricalFullBookAcquisitionLedger"))]),
            }
        )
    candidate_rows = context.get("candidate_rows", [])
    acquired_count = 0
    acquisition_records = acquisition if isinstance(acquisition, list) else []
    auth_required_count = sum(
        1
        for row in list(candidate_rows) + acquisition_records
        if "AUTH_REQUIRED" in str(row.get("candidate_state") or row.get("acquisition_result") or row.get("exact_gap_or_auth_reason"))
    )
    classification_counts = Counter(row["classification_state"] for row in rows)
    summary = {
        "historical_full_book_verified_public_endpoint_found_flag": False,
        "historical_full_book_verified_public_dataset_found_flag": False,
        "historical_full_book_verified_public_rows_count": 0,
        "historical_full_book_verified_public_market_count": 0,
        "historical_full_book_verified_public_venue_count": 0,
        "historical_full_book_candidate_nonofficial_source_count": len(candidate_rows),
        "historical_full_book_candidate_nonofficial_acquired_rows_count": acquired_count,
        "historical_full_book_reconstructed_candidate_rows_count": 0,
        "historical_full_book_auth_required_count": auth_required_count,
        "historical_full_book_public_unavailable_count": classification_counts["HISTORICAL_FULL_BOOK_PUBLIC_UNAVAILABLE"],
        "forward_l2_capture_start_count": inventory.get("total_forward_l2_row_count", 0),
        "forward_l2_rows_count": inventory.get("total_forward_l2_row_count", 0),
        "forward_l2_market_count": inventory.get("total_forward_l2_row_count", 0),
        "GFP2R_historical_full_book_assumption_allowed_flag": False,
        "GFP2R_allowed_substitute_inputs": [
            "current_book",
            "forward_l2_after_capture_start",
            "historical_trades",
            "candles",
            "price_history",
            "lifecycle",
            "resolution",
        ],
        "GFP2R_forbidden_assumptions": [
            "historical_full_book_exists",
            "current_snapshot_is_historical_book",
            "trade_history_is_full_book",
            "candles_are_full_book",
            "forward_l2_before_capture_start",
            "reconstructed_book_is_source_truth",
        ],
        "classification_counts": dict(sorted(classification_counts.items())),
        **route_defaults("source_evidence", data1_refs=[generated_ref(report_path("PR168_DATA1_HistoricalFullBookAvailabilityAudit"))]),
    }
    return summary, rows
