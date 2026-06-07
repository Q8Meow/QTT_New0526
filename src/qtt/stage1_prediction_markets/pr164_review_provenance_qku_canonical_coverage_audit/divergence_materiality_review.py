"""PR163-B divergence materiality review."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import DIVERGENCE_MATERIALITY, require_enum
from .deterministic_ids import plain_ref


def classify_divergence_materiality(row: dict[str, Any]) -> str:
    classes = set(row.get("divergence_classes") or [])
    if {"LIFECYCLE_DIVERGENCE", "FILL_INTEGRITY_REVIEW_REQUIRED"} & classes:
        return "TRADING_MATERIAL_DIVERGENCE"
    if {"FEE_DIVERGENCE", "FILL_PRICE_DIVERGENCE"} & classes:
        return "EXECUTION_COST_MATERIAL_DIVERGENCE"
    if "LATENCY_DIVERGENCE" in classes:
        return "LATENCY_MATERIAL_DIVERGENCE"
    if "DATA_QUALITY_DIVERGENCE" in classes:
        return "SOURCE_QUALITY_MATERIAL_DIVERGENCE"
    return "BENIGN_EXPECTED_SYNTHETIC_DIVERGENCE"


def build_divergence_materiality_rows(divergence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(sorted(divergence_rows, key=lambda item: item["candidate_packet_id"]), 1):
        materiality = require_enum(classify_divergence_materiality(row), DIVERGENCE_MATERIALITY, "divergence_materiality")
        rows.append(
            {
                "divergence_materiality_record_ref": plain_ref("DIVERGENCE_MATERIALITY", index),
                "candidate_id": row["candidate_packet_id"],
                "qku_ids": row.get("qku_ids") or [],
                "divergence_ref": row.get("divergence_ref", ""),
                "divergence_classes": row.get("divergence_classes") or [],
                "divergence_materiality": materiality,
                "exact_materiality_reason": f"PR163-B divergence classes routed to {materiality}.",
                "downstream_pr_route": (
                    "ROUTE_TO_PR163_C_INFRA_REPAIR"
                    if materiality == "REPAIRABLE_INFRASTRUCTURE_DIVERGENCE"
                    else "ROUTE_TO_PR165_SCORING"
                ),
                "validation_status": "PASS",
            }
        )
    return rows
