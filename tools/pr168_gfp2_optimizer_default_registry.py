#!/usr/bin/env python3
"""Optimizer default and parameter range seed registry for PR168-GFP2."""

from __future__ import annotations

from typing import Any


PARAMETER_FAMILIES = (
    "probability_calibration",
    "confidence_lcb",
    "fdr_control",
    "purged_walk_forward_cpcv",
    "capacity_participation",
    "fill_probability",
    "slippage_adverse_selection",
    "latency_decay",
    "portfolio_risk_aversion",
    "correlation_cluster",
    "no_trade_margin",
    "scenario_ladder",
    "order_policy_selection",
    "limit_price_offset",
    "order_size_bucket",
    "risk_budget_bucket",
    "quantum_penalty_scaling",
    "qubo_variable_encoding",
    "bqm_cqm_ising_mapping",
    "classical_fallback_optimizer",
)


def optimizer_default_rows() -> list[dict[str, Any]]:
    return [
        {
            "parameter_name": family,
            "parameter_family": family,
            "classical_or_quantum_or_hybrid": "quantum_or_hybrid"
            if "quantum" in family or "qubo" in family or "bqm" in family
            else "classical",
            "candidate_range_or_default": "DEFAULT_PENDING_SOURCE_OR_OWNER_DECISION",
            "range_scale": "PENDING",
            "units": "PENDING",
            "source_ref": "PR168_GFP2_EXTERNAL_SOURCE_OR_OWNER_DECISION_REQUIRED",
            "source_tier": "GAP_ROUTED",
            "accepted_truth_flag": False,
            "candidate_only_flag": True,
            "optimizer_default_flag": False,
            "owner_override_allowed_flag": True,
            "consumer_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Governance Agent",
            "repair_route_if_missing": "PR168_GFP2_OptimizerDefaultAndParameterRangeSeed.report.json",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for family in PARAMETER_FAMILIES
    ]
