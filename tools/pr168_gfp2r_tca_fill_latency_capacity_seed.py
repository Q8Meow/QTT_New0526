#!/usr/bin/env python3
"""TCA, fill, latency, and capacity seed rows for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def build_tca_fill_latency_capacity_rows(stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, stack in enumerate(stack_rows, start=1):
        rows.append(
            {
                "row_id": f"tca_fill_latency_capacity_seed_{index:05d}",
                "candidate_stack_id": stack["candidate_stack_id"],
                "compute_row_id": stack["compute_row_id"],
                "tca_component_refs": stack.get("tca_component_refs", []),
                "implementation_shortfall_seed_state": "REPAIR_REQUIRED_RP2",
                "spread_cost_seed_state": "AVAILABLE_WHEN_SPREAD_VARIANT_EXECUTED_ELSE_GAP",
                "slippage_depth_curve_seed_state": "DATA1A_DEPTH_SEED_ONLY",
                "fill_probability_seed_state": "MISSING_FILL_MODEL_REPAIR_REQUIRED",
                "latency_decay_seed_state": stack.get("latency_input_readiness"),
                "capacity_depth_penalty_seed_state": stack.get("capacity_crowding_status"),
                "calibration_seed_state": "CALIBRATION_SAMPLE_SIZE_GAP",
                "candidate_only_flag": True,
                **route_defaults(
                    "risk",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    upstream_refs=[stack["candidate_stack_id"]],
                ),
            }
        )
    return rows
