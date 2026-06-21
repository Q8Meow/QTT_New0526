#!/usr/bin/env python3
"""QKU/formula/data-consumer bridge for PR168-DATA1A."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


DATA_FAMILY_TO_VARIABLES = {
    "orderbook": {"ask", "bid", "market_price", "spread_cost", "slippage_cost", "fill_probability", "capacity_limit"},
    "trade_history": {"market_implied_probability", "market_price"},
    "price_history": {"market_implied_probability", "market_price"},
    "fee_cost": {"fee_rate"},
    "latency": {"latency_ms"},
    "portfolio": {"portfolio_marginal_utility"},
    "fdr": {"overfit_fdr_penalty"},
    "probability": {"predicted_probability"},
    "quantity": {"quantity"},
}


def _load_records(context: dict[str, Any], report_id: str) -> list[dict[str, Any]]:
    records = context["reports"].get(report_id, {}).get("records", [])
    return records if isinstance(records, list) else []


def _available_components(inventory: dict[str, Any]) -> set[str]:
    available = set()
    if inventory.get("total_orderbook_snapshot_row_count", 0):
        available.add("orderbook")
    if inventory.get("total_historical_trade_row_count", 0):
        available.add("trade_history")
    if inventory.get("total_price_history_or_candle_point_count", 0):
        available.add("price_history")
    if inventory.get("total_forward_l2_row_count", 0):
        available.add("forward_l2")
    if inventory.get("polymarket_unique_token_or_asset_count", 0):
        available.add("fee_tick_min_size_partial")
    return available


def build_qku_unblock_bridge(context: dict[str, Any], inventory: dict[str, Any], created_at_utc: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gfp_rows = _load_records(context, "PR168_GFP_QKUComputationCoverage")
    if not gfp_rows:
        # PR168-GFP is a prior artifact, not a DATA1 required artifact; load from context reports only when present.
        try:
            import json

            path = report_path("PR168_GFP_QKUComputationCoverage")
            if path.exists():
                gfp_rows = json.loads(path.read_text(encoding="utf-8")).get("records", [])
        except Exception:  # noqa: BLE001 - absence becomes gap routed
            gfp_rows = []
    rp_gap_rows: list[dict[str, Any]] = []
    try:
        import json

        path = report_path("PR168_RP_ActionableInputGapQueue")
        if path.exists():
            rp_gap_rows = json.loads(path.read_text(encoding="utf-8")).get("records", [])
    except Exception:  # noqa: BLE001
        rp_gap_rows = []

    available = _available_components(inventory)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(gfp_rows[:10], start=1):
        formula_ids = source.get("formula_ids") or [source.get("formula_id")]
        qku_id = str(source.get("canonical_row_key", "")).split("QKU::")[-1] or source.get("qku_id")
        missing_components = [
            "predicted_probability",
            "formula_input_binding",
            "source_evidence_acceptance",
            "historical_full_book_if_formula_demands_it",
        ]
        if "orderbook" in available:
            state = "DATA1_PARTIALLY_UNBLOCKED_MISSING_COMPONENTS"
            confidence = "UNBLOCK_CONFIDENCE_MEDIUM"
            match_state = "EXACT_QKU_FORMULA_MATCH"
            now_computable = False
        else:
            state = "STILL_BLOCKED_FORMULA_INPUT_BINDING_REQUIRED"
            confidence = "UNBLOCK_CONFIDENCE_NONE"
            match_state = "NO_MATCH_REQUIRES_GFP2R_MAPPING_REPAIR"
            now_computable = False
        rows.append(
            {
                "qku_unblock_row_id": f"qku_unblock_{index:05d}",
                "qku_id": qku_id,
                "formula_id_if_available": source.get("formula_id"),
                "formula_ids_if_available": formula_ids,
                "candidate_id_if_available": None,
                "algorithm_id_if_available": None,
                "candidate_stack_id_if_available": None,
                "previous_block_state": source.get("real_computation_evidence_status"),
                "previous_block_report_ref": generated_ref(report_path("PR168_GFP_QKUComputationCoverage")),
                "missing_data_components_before_data1": ["numeric_market_data_inputs", "formula_input_values"],
                "DATA1_snapshot_refs": [
                    "docs/master_plan/generated/pr168_data1_snapshots/kalshi/kalshi_snapshots.jsonl",
                    "docs/master_plan/generated/pr168_data1_snapshots/polymarket/polymarket_snapshots.jsonl",
                ],
                "DATA1_feature_refs": context["reports"]
                .get("PR168_DATA1_NormalizedMarketDataFeatureRegistry", {})
                .get("computed_feature_refs", [])[:20],
                "DATA1_handoff_refs": [
                    generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse")),
                    generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch")),
                    generated_ref(report_path("PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch")),
                ],
                "after_data1_unblock_state": state,
                "match_state": match_state,
                "now_computable_candidate_flag": now_computable,
                "accepted_truth_flag": False,
                "source_evidence_acceptance_required_flag": True,
                "remaining_missing_components": missing_components,
                "historical_full_book_required_flag": True,
                "historical_full_book_available_flag": False,
                "historical_full_book_gap_route": "USE_CURRENT_BOOK_FORWARD_L2_TRADES_CANDLES_PRICE_HISTORY_ONLY_UNTIL_DATA1B_OR_SOURCE_REVIEW",
                "GFP2R_allowed_data_route": "candidate_only_current_book_forward_l2_trade_price_history",
                "RP2_allowed_data_route": "replay_paper_candidate_with_DATA1_substitutes_and_bias_flags",
                "RANK2_allowed_data_route": "quality_scored_candidate_ranking_seed_only",
                "unblock_confidence_tier": confidence,
                "unblock_confidence_reason": "exact QKU/formula exists, but market/data-family input binding remains a GFP2R repair",
                "GFP2R_formula_binding_repair_required_flag": True,
                "false_precision_blocked_flag": True,
                "created_at_utc": created_at_utc,
                **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
            }
        )
    for offset, gap in enumerate(rp_gap_rows[:5], start=len(rows) + 1):
        missing_variables = set(gap.get("missing_variables") or [])
        data1_covered = sorted(
            family for family, variables in DATA_FAMILY_TO_VARIABLES.items() if missing_variables & variables and family in available
        )
        rows.append(
            {
                "qku_unblock_row_id": f"qku_unblock_{offset:05d}",
                "qku_id": gap.get("qku_id"),
                "formula_id_if_available": gap.get("formula_id"),
                "formula_ids_if_available": [gap.get("formula_id")],
                "candidate_id_if_available": None,
                "algorithm_id_if_available": None,
                "candidate_stack_id_if_available": None,
                "previous_block_state": gap.get("computed_status"),
                "previous_block_report_ref": generated_ref(report_path("PR168_RP_ActionableInputGapQueue")),
                "missing_data_components_before_data1": sorted(missing_variables),
                "DATA1_snapshot_refs": [generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))],
                "DATA1_feature_refs": context["reports"].get("PR168_DATA1_NormalizedMarketDataFeatureRegistry", {}).get("computed_feature_refs", [])[:20],
                "DATA1_handoff_refs": [generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))],
                "after_data1_unblock_state": "DATA1_PARTIALLY_UNBLOCKED_MISSING_COMPONENTS"
                if data1_covered
                else "STILL_BLOCKED_FORMULA_INPUT_BINDING_REQUIRED",
                "match_state": "DATA_CONSUMER_REQUIREMENT_MATCH_ONLY",
                "now_computable_candidate_flag": False,
                "accepted_truth_flag": False,
                "source_evidence_acceptance_required_flag": True,
                "remaining_missing_components": sorted(missing_variables - set().union(*(DATA_FAMILY_TO_VARIABLES.get(family, set()) for family in data1_covered))),
                "historical_full_book_required_flag": "historical_full_book" in missing_variables,
                "historical_full_book_available_flag": False,
                "historical_full_book_gap_route": "DATA1B_OR_HISTORICAL_L2_ACQUISITION_REVIEW",
                "GFP2R_allowed_data_route": "repair_queue_seed_only",
                "RP2_allowed_data_route": "repair_before_retest",
                "RANK2_allowed_data_route": "do_not_rank_as_exact_qku_proof",
                "unblock_confidence_tier": "UNBLOCK_CONFIDENCE_LOW",
                "unblock_confidence_reason": "inferred data-consumer requirement only; not exact QKU proof input",
                "GFP2R_formula_binding_repair_required_flag": True,
                "false_precision_blocked_flag": True,
                "created_at_utc": created_at_utc,
                **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
            }
        )

    state_counts = Counter(row["after_data1_unblock_state"] for row in rows)
    confidence_counts = Counter(row["unblock_confidence_tier"] for row in rows)
    exact_gfp_qkus = {row["qku_id"] for row in rows if row.get("match_state") == "EXACT_QKU_FORMULA_MATCH"}
    summary = {
        "qku_missing_data_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_formula_input_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_orderbook_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_trade_history_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_price_history_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_fee_cost_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_resolution_lifecycle_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_historical_full_book_blocked_before_data1_count": len(exact_gfp_qkus),
        "qku_now_computable_after_data1_public_candidate_data_count": 0,
        "qku_now_partially_computable_after_data1_count": state_counts["DATA1_PARTIALLY_UNBLOCKED_MISSING_COMPONENTS"],
        "qku_still_blocked_after_data1_count": len(rows),
        "qku_still_blocked_historical_full_book_count": len(exact_gfp_qkus),
        "qku_still_blocked_source_acceptance_required_count": len(rows),
        "qku_still_blocked_formula_input_binding_count": len(rows),
        "qku_still_blocked_fee_cost_resolution_latency_count": len(rows),
        "qku_still_blocked_forecastex_ibkr_auth_count": 0,
        "exact_qku_unblocked_count": 0,
        "exact_formula_unblocked_count": 0,
        "exact_qku_formula_pair_unblocked_count": 0,
        "inferred_data_consumer_unblocked_count": state_counts["DATA1_PARTIALLY_UNBLOCKED_MISSING_COMPONENTS"],
        "qku_unblock_count_with_exact_previous_block_ref": len(exact_gfp_qkus),
        "qku_unblock_count_without_previous_block_ref_gap_routed": len([row for row in rows if not row.get("previous_block_report_ref")]),
        "qku_unblock_false_precision_blocked_count": len([row for row in rows if row.get("false_precision_blocked_flag")]),
        "qku_unblock_confidence_high_count": confidence_counts["UNBLOCK_CONFIDENCE_HIGH"],
        "qku_unblock_confidence_medium_count": confidence_counts["UNBLOCK_CONFIDENCE_MEDIUM"],
        "qku_unblock_confidence_low_count": confidence_counts["UNBLOCK_CONFIDENCE_LOW"],
        "qku_unblock_confidence_none_count": confidence_counts["UNBLOCK_CONFIDENCE_NONE"],
        "state_counts": dict(sorted(state_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "count_precision_note": "No exact QKU is declared fully unblocked because DATA1 lacks exact QKU-to-market/formula input binding.",
        **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
    }
    return summary, rows
