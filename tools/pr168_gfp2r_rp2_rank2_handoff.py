#!/usr/bin/env python3
"""RP2 and RANK2 candidate handoff rows for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_rp2_handoff_rows(execution_rows: list[dict[str, Any]], threshold_rows: list[dict[str, Any]], tca_rows: list[dict[str, Any]], scenario_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    threshold_by_compute = {row["compute_row_id"]: row for row in threshold_rows}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate([r for r in execution_rows if r.get("compute_lane") == "PROVISIONAL_DATA_CONSUMER"], start=1):
        rows.append(
            {
                "rp2_candidate_row_id": f"rp2_candidate_{index:05d}",
                "compute_row_id": row["compute_row_id"],
                "compute_lane": row.get("compute_lane"),
                "qku_id": row.get("qku_id"),
                "formula_id": row.get("formula_id"),
                "formula_variant_id": row.get("formula_variant_id"),
                "venue": row.get("venue"),
                "market_id_or_token_id": row.get("market_id_or_token_id"),
                "side": row.get("side"),
                "formula_output_refs": [row.get("formula_execution_receipt_ref")] if row.get("formula_execution_receipt_ref") else [],
                "break_even_threshold_refs": [threshold_by_compute[row["compute_row_id"]]["break_even_row_id"]]
                if row["compute_row_id"] in threshold_by_compute
                else [],
                "DATA1_snapshot_refs": row.get("DATA1_snapshot_refs", []),
                "DATA1A_quality_refs": ["PR168_DATA1A_DataQualityCoverageAudit"],
                "tca_seed_refs": [item.get("row_id") for item in tca_rows[:1]],
                "fill_latency_capacity_seed_refs": [item.get("row_id") for item in tca_rows[:1]],
                "scenario_ladder_seed_refs": [item.get("row_id") for item in scenario_rows[:1]],
                "missing_inputs": ["independent_probability_model", "fill_probability", "slippage_depth_curve"],
                "repair_routes": [
                    "BIND_INDEPENDENT_PROBABILITY_MODEL",
                    "RP2_FILL_SLIPPAGE_LATENCY_RECOMPUTE",
                    "SOURCE_EVIDENCE_ACCEPTANCE_REVIEW",
                ],
                "candidate_only_flag": True,
                "provisional_flag": True,
                "real_positive_negative_allowed_flag": False,
                **route_defaults(
                    "replay",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[str(row.get("formula_variant_id"))],
                    upstream_refs=[row["compute_row_id"]],
                ),
            }
        )
    return rows


def build_rank2_handoff_rows(stack_rows: list[dict[str, Any]], quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    quantum_by_stack = {row["candidate_stack_ref"]: row for row in quantum_rows}
    rows: list[dict[str, Any]] = []
    for index, stack in enumerate(stack_rows, start=1):
        quantum = quantum_by_stack.get(stack["candidate_stack_id"], {})
        rows.append(
            {
                "rank2_candidate_row_id": f"rank2_candidate_{index:05d}",
                "candidate_stack_id": stack["candidate_stack_id"],
                "compute_row_id": stack["compute_row_id"],
                "compute_lane": stack.get("compute_lane"),
                "candidate_execution_adjusted_edge_ref": stack.get("candidate_execution_adjusted_edge"),
                "candidate_fill_adjusted_expected_pnl_ref": stack.get("candidate_fill_adjusted_expected_pnl"),
                "candidate_lcb_edge_ref": stack.get("candidate_lcb_edge"),
                "candidate_no_trade_margin_ref": stack.get("candidate_no_trade_margin"),
                "break_even_probability_ref": stack.get("break_even_probability_after_costs"),
                "required_probability_edge_ref": stack.get("required_probability_edge"),
                "portfolio_marginal_utility_ref": stack.get("portfolio_marginal_utility_cluster_id"),
                "overfit_fdr_ref": stack.get("overfit_fdr_trial_family_id"),
                "capacity_crowding_ref": stack.get("capacity_crowding_status"),
                "regime_condition_ref": stack.get("regime_condition_id"),
                "quantum_candidate_stack_ref": quantum.get("quantum_mapping_id"),
                "no_trade_baseline_ref": stack.get("no_trade_baseline_ref"),
                "candidate_only_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                **route_defaults(
                    "ranking",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[str(stack.get("formula_variant_id"))],
                    upstream_refs=[stack["candidate_stack_id"], stack["compute_row_id"]],
                ),
            }
        )
    return rows
