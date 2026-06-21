#!/usr/bin/env python3
"""DATA1A allowed-data-family contract consumption for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import ALLOWED_DATA_FAMILIES, route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_allowed_data_family_consumption_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    contract = context["data1a_reports"].get("PR168_DATA1A_GFP2RAllowedDataFamilyContract", {})
    data1a_allowed = set(contract.get("allowed_data_families", [])) if isinstance(contract, dict) else set()
    alias_map = {
        "current_orderbook_snapshot": "current_book",
        "historical_candle": "candlestick_history",
        "market_candle": "candlestick_history",
        "resolution_or_settlement_if_present": "resolution_inputs",
        "fee_tick_min_size_if_present": "tick_size_min_order_size_when_present",
        "data_quality_score_non_proof": "data_quality_score_non_proof",
        "recent_trade": "historical_trade",
    }
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(ALLOWED_DATA_FAMILIES, start=1):
        data1a_name = alias_map.get(family, family)
        allowed = data1a_name in data1a_allowed or family == "data_quality_score_non_proof"
        rows.append(
            {
                "row_id": f"allowed_data_family_consumption_{index:05d}",
                "data_family": family,
                "DATA1A_source_ref": "PR168_DATA1A_GFP2RAllowedDataFamilyContract",
                "DATA1A_contract_family_name": data1a_name,
                "allowed_for_candidate_compute_flag": allowed,
                "allowed_for_provisional_compute_flag": allowed,
                "allowed_for_real_positive_negative_proof_flag": False,
                "allowed_for_RP2_recompute_flag": allowed,
                "allowed_for_RANK2_ranking_flag": allowed,
                "historical_full_book_substitute_flag": family
                in {
                    "current_orderbook_snapshot",
                    "forward_l2_after_capture_start",
                    "historical_trade",
                    "historical_candle",
                    "market_candle",
                    "price_history",
                },
                "substitute_limitations": [
                    "candidate_only_non_proof",
                    "not_accepted_source_truth",
                    "not_historical_full_book_replay",
                ],
                "required_repair_if_missing": "ROUTE_TO_DATA1B_OR_SOURCE_EVIDENCE_REVIEW",
                **route_defaults(
                    "market_data",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    upstream_refs=["PR168_DATA1A_GFP2RAllowedDataFamilyContract"],
                ),
            }
        )
    return rows


def data1a_consumption_summary(context: dict[str, Any]) -> dict[str, Any]:
    final = context["data1a_reports"].get("PR168_DATA1A_FinalSummary", {})
    return {
        "data1a_consumed_flag": True,
        "historical_full_book_verified_public_rows": final.get("historical_full_book_verified_public_rows_count", 0),
        "GFP2R_historical_full_book_assumption_allowed_flag": final.get(
            "GFP2R_historical_full_book_assumption_allowed_flag", False
        ),
        "exact_qku_formula_unblocked_count": final.get("exact_qku_unblocked_count", 0),
        "partial_or_candidate_computability_rows": final.get("qku_now_partially_computable_after_data1_count", 0),
        "still_blocked_or_repair_routed_rows": final.get("qku_still_blocked_after_data1_count", 0),
        "false_precision_blocked_rows": final.get("qku_unblock_false_precision_blocked_count", 0),
    }
