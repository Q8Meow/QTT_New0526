#!/usr/bin/env python3
"""Downstream DATA1 first-batch selectors."""

from __future__ import annotations

from tools.pr168_data1_config import authority_flags, route_defaults


def build_priority_rows(snapshot_rows: list[dict[str, object]], feature_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    rows = []
    orderbook_rows = [row for row in snapshot_rows if row.get("data_family") == "current_full_orderbook_snapshot"]
    for index, snapshot in enumerate(orderbook_rows, start=1):
        feature_refs = [feature["feature_row_id"] for feature in feature_rows if snapshot["snapshot_row_id"] in feature.get("snapshot_row_refs", [])]
        rows.append(
            {
                "priority_row_id": f"data_binding_priority_{index:04d}",
                "venue": snapshot["venue"],
                "market_or_token_ref": snapshot.get("ticker") or snapshot.get("token_id_or_asset_id") or snapshot.get("market_id"),
                "snapshot_refs": [snapshot["snapshot_row_id"]],
                "feature_refs": feature_refs,
                "priority_score_non_proof": round(1.0 + len(feature_refs) / 10.0, 4),
                "priority_reason_codes": [
                    "active_or_open_status",
                    "orderbook_available",
                    "forward_l2_available",
                    "historical_full_book_gap_routed",
                    "expected_downstream_formula_replay_ranking_unblock",
                ],
                "expected_downstream_unblock_count": 3,
                "qku_formula_coverage_refs_if_available": ["PR168-GFP2R"],
                "candidate_stack_relevance_refs_if_available": ["PR168-RP2", "PR168-RANK2"],
                "market_selection_diversity_bucket": str(snapshot["venue"]),
                "venue_selection_diversity_bucket": str(snapshot["venue"]),
                "historical_full_book_priority_flag": True,
                "forward_l2_capture_priority_flag": True,
                "created_at_utc": now_utc,
                **route_defaults("ranking"),
                **authority_flags(),
            }
        )
    return rows


def build_gfp2r_handoff(snapshot_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], feature_rows: list[dict[str, object]], readiness_rows: list[dict[str, object]], now_utc: str) -> dict[str, object]:
    return {
        "handoff_id": "pr168_data1_gfp2r_data_ready_formula_universe",
        "data_ready_market_count": sum(1 for row in snapshot_rows if row.get("data_family") == "market_metadata"),
        "data_ready_orderbook_snapshot_count": sum(1 for row in snapshot_rows if row.get("data_family") == "current_full_orderbook_snapshot"),
        "data_ready_forward_l2_count": len(l2_rows),
        "data_ready_historical_full_book_count": 0,
        "data_ready_price_history_count": sum(1 for row in snapshot_rows if "price" in str(row.get("data_family")) or "candle" in str(row.get("data_family"))),
        "data_ready_trade_history_count": sum(1 for row in snapshot_rows if "trade" in str(row.get("data_family"))),
        "candidate_only_data_count": len(snapshot_rows) + len(l2_rows),
        "acceptance_pending_count": sum(1 for row in readiness_rows if "ACCEPTANCE" in str(row.get("data_readiness_state"))),
        "auth_required_count": sum(1 for row in readiness_rows if "AUTH" in str(row.get("data_readiness_state"))),
        "unavailable_count": sum(1 for row in readiness_rows if "UNAVAILABLE" in str(row.get("data_readiness_state"))),
        "formula_input_unblock_candidates": [feature["feature_row_id"] for feature in feature_rows[:20]],
        "qku_family_unblock_candidates": ["market_microstructure", "price_history", "trade_history", "cost_capacity"],
        "proof_state": "DATA_READY_CANDIDATE_NOT_PROFIT_PROOF",
        "source_evidence_acceptance_required_flag": True,
        "created_at_utc": now_utc,
        **route_defaults("market_data"),
        **authority_flags(),
    }


def build_rp2_batch(priority_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    rows = []
    for index, priority in enumerate(priority_rows[:4], start=1):
        venue = str(priority["venue"])
        rows.append(
            {
                "batch_id": "pr168_data1_rp2_first_replay_paper_batch",
                "batch_row_id": f"rp2_batch_row_{index:04d}",
                "venue": venue,
                "market_id": priority["market_or_token_ref"],
                "ticker_or_token_id": priority["market_or_token_ref"],
                "snapshot_refs": priority["snapshot_refs"],
                "l2_replay_refs": [row["l2_replay_row_id"] for row in l2_rows if row["venue"] == venue],
                "feature_refs": priority["feature_refs"],
                "needed_formula_refs_if_available": ["PR168-GFP2R"],
                "why_selected": priority["priority_reason_codes"],
                "priority_score_non_proof": priority["priority_score_non_proof"],
                "tca_inputs_available": True,
                "fill_inputs_available": True,
                "latency_inputs_available": True,
                "capacity_inputs_available": True,
                "calibration_inputs_available": True,
                "historical_full_book_available": False,
                "forward_l2_available": True,
                "scenario_ladder_inputs_available": True,
                "missing_inputs": ["historical_full_book_replay"],
                "created_at_utc": now_utc,
                **route_defaults("replay"),
                **authority_flags(),
            }
        )
    return rows


def build_rank2_batch(priority_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    rows = []
    for index, priority in enumerate(priority_rows[:4], start=1):
        rows.append(
            {
                "rank_batch_id": "pr168_data1_rank2_first_evidence_ranking_batch",
                "rank_batch_row_id": f"rank2_batch_row_{index:04d}",
                "candidate_stack_data_refs": priority["snapshot_refs"] + priority["feature_refs"],
                "no_trade_baseline_refs": ["NO_TRADE_BASELINE_PERMANENT_COMPETITOR"],
                "execution_adjusted_ranking_seed_inputs": ["spread", "depth", "fillable_size_at_edge_band", "data_staleness_penalty_seed"],
                "portfolio_marginal_utility_seed_inputs": ["venue", "event_family", "category", "data_quality_score"],
                "capacity_crowding_seed_inputs": ["depth_at_best", "depth_within_edge_band", "participation_rate_candidate"],
                "overfit_fdr_seed_inputs": ["trial_family_candidate_id", "fdr_family_id", "sample_size_seed"],
                "regime_condition_seed_inputs": ["liquidity_regime", "spread_regime", "volatility_regime", "time_to_resolution_regime"],
                "historical_full_book_quality_inputs": ["historical_full_book_gap_flag"],
                "forward_l2_quality_inputs": ["forward_l2_capture_available_flag"],
                "champion_challenger_seed_only_flag": True,
                "created_at_utc": now_utc,
                **route_defaults("ranking"),
                **authority_flags(),
            }
        )
    return rows
