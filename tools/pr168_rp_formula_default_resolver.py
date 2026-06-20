#!/usr/bin/env python3
"""Default and threshold resolution for PR168-RP."""

from __future__ import annotations

from typing import Any


MISSING_DEFAULTS = (
    "positive_edge_threshold",
    "minimum_action_margin",
    "confidence_multiplier",
    "tail_risk_budget",
)


def resolve_default_stack(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_resolution_status": "MISSING_DEFAULTS_ROUTED",
        "missing_defaults": list(MISSING_DEFAULTS),
        "default_gap_reason_codes": ["MISSING_DEFAULT_THRESHOLD"],
        "thresholds_resolved": False,
        "threshold_source_ref": None,
        "row_ref": row.get("canonical_row_key"),
    }


def default_gap_row(source: dict[str, Any]) -> dict[str, Any]:
    stack = source.get("default_stack") or resolve_default_stack(source)
    return {
        "canonical_row_key": source.get("canonical_row_key"),
        "qku_id": source.get("qku_id"),
        "row_family": source.get("row_family"),
        "formula_id": source.get("formula_id"),
        "required_formula_set_id": source.get("required_formula_set_id"),
        "missing_defaults": stack["missing_defaults"],
        "gap_reason_code": "MISSING_DEFAULT_THRESHOLD",
        "critical": True,
        "owning_agent": "Governance Agent",
        "downstream_route": "PR168_RP_MissingDefaultResolutionQueue.report.json",
        "replay_paper_required_before_promotion": True,
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "live_authority": False,
        "producer": "PR168_RP_DEFAULT_RESOLVER",
        "consumer": "PR168_RP_FORMULA_COMPUTE_KERNEL",
        "no_orphan_status": "CONNECTED_TO_MISSING_DEFAULT_QUEUE",
    }
