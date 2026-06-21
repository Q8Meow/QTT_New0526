#!/usr/bin/env python3
"""Execution-adjusted candidate stack seeds for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def _value(row: dict[str, Any], key: str) -> float | None:
    values = row.get("computed_values", {})
    value = values.get(key) if isinstance(values, dict) else None
    return float(value) if value is not None else None


def build_execution_adjusted_seed_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate([r for r in execution_rows if r.get("formula_executed_flag")], start=1):
        required_edge = _value(row, "required_probability_edge")
        break_even = _value(row, "break_even_probability_after_costs")
        no_trade_threshold = _value(row, "no_trade_threshold")
        cost = no_trade_threshold if no_trade_threshold is not None else max(0.0, required_edge or 0.0)
        candidate_stack_id = f"gfp2r_candidate_stack_{index:05d}"
        rows.append(
            {
                "candidate_stack_id": candidate_stack_id,
                "compute_row_id": row["compute_row_id"],
                "qku_id": row.get("qku_id"),
                "formula_id": row.get("formula_id"),
                "formula_variant_id": row.get("formula_variant_id"),
                "algorithm_id_if_available": None,
                "venue": row.get("venue"),
                "market_id_or_token_id": row.get("market_id_or_token_id"),
                "side": row.get("side"),
                "order_policy": "no_trade" if row.get("independent_probability_missing_flag") else "maker_limit",
                "order_size_bucket": "min_size_or_one_contract",
                "entry_price_bucket": "DATA1A_public_candidate_entry_price",
                "liquidity_bucket": "DATA1A_depth_seed",
                "spread_bucket": "DATA1A_spread_seed_or_gap",
                "latency_bucket": "DATA1A_snapshot_staleness_seed",
                "capacity_bucket": "DATA1A_depth_capacity_seed",
                "regime_condition_id": f"regime::{row.get('venue')}::candidate_public_snapshot",
                "data_quality_tier": "DATA1A_TIER_A_OR_B_CANDIDATE",
                "candidate_output_classification": row.get("candidate_output_classification"),
                "quantum_mapping_id_if_any": f"quantum_map::{candidate_stack_id}",
                "compute_lane": row.get("compute_lane"),
                "candidate_execution_adjusted_edge": None,
                "candidate_fill_adjusted_expected_pnl": None,
                "candidate_net_expected_pnl": None,
                "candidate_lcb_edge": None,
                "candidate_no_trade_margin": round(-abs(cost or 0.0), 6),
                "break_even_probability_after_costs": break_even,
                "required_probability_edge": required_edge,
                "tca_component_refs": [row["compute_row_id"]],
                "fill_input_readiness": "FILL_MODEL_REPAIR_REQUIRED",
                "latency_input_readiness": "LATENCY_DECAY_SEED_ONLY",
                "capacity_crowding_status": "CAPACITY_SEED_ONLY",
                "overfit_fdr_trial_family_id": f"trial_family::{row.get('formula_variant_id')}",
                "portfolio_marginal_utility_cluster_id": f"portfolio_cluster::{row.get('venue')}::{row.get('market_id_or_token_id')}",
                "scenario_ladder_seed_ref": f"scenario_ladder::{candidate_stack_id}",
                "calibration_seed_ref": f"calibration_gap::{candidate_stack_id}",
                "no_trade_baseline_ref": "NO_TRADE_BASELINE_PERMANENT_COMPETITOR",
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                "candidate_only_flag": True,
                **route_defaults(
                    "ranking",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[str(row.get("formula_variant_id"))],
                    numeric_evidence_refs=row.get("numeric_evidence_refs", []),
                    upstream_refs=[row["compute_row_id"]],
                ),
            }
        )
    return rows
