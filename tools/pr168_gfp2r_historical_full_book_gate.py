#!/usr/bin/env python3
"""Historical full-book blocker and repair routing for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_historical_full_book_repair_rows(mapping_rows: list[dict[str, Any]], variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for source in [*mapping_rows, *variants]:
        if source.get("historical_full_book_required_flag") and not source.get("historical_full_book_available_flag"):
            index += 1
            rows.append(
                {
                    "row_id": f"historical_full_book_repair_{index:05d}",
                    "source_row_ref": source.get("mapping_row_id") or source.get("formula_variant_id"),
                    "qku_id": source.get("qku_id"),
                    "formula_id": source.get("formula_id"),
                    "formula_variant_id": source.get("formula_variant_id"),
                    "historical_full_book_required_flag": True,
                    "historical_full_book_available_flag": False,
                    "historical_full_book_assumption_used_flag": False,
                    "historical_full_book_forbidden_violation_flag": False,
                    "repair_route": "ROUTE_TO_DATA1B_OR_HISTORICAL_L2_ACQUISITION_REVIEW",
                    "substitute_limitations": [
                        "current_orderbook_snapshot_is_not_historical_full_book",
                        "trades_candles_price_history_are_substitutes_only",
                    ],
                    **route_defaults(
                        "source_evidence",
                        data1_refs=data1_report_refs(),
                        data1a_refs=data1a_report_refs(),
                        upstream_refs=[str(source.get("mapping_row_id") or source.get("formula_variant_id"))],
                    ),
                }
            )
    return rows
