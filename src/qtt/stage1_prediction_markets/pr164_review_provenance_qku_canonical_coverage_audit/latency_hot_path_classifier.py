"""Latency and hot-path classifier."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import LATENCY_CLASSES, require_enum
from .deterministic_ids import plain_ref


def latency_class_for(computability: dict[str, Any], candidate: dict[str, Any] | None) -> str:
    if computability["activation_state"] == "DORMANT_NON_STAGE1_MARKET":
        return "NOT_LATENCY_SAFE_FOR_STAGE1"
    if not candidate:
        return "REQUIRES_CACHE_BEFORE_RUNTIME"
    if candidate.get("candidate_type") == "QUANTUM_FORMULATION":
        return "CONTROL_PLANE_ONLY"
    if candidate.get("precompute_allowed") and candidate.get("cacheable"):
        return "HOT_PATH_SAFE_PRECOMPUTED_ONLY"
    return "REPLAY_PAPER_ONLY"


def build_latency_rows(
    computability_rows: list[dict[str, Any]],
    candidate_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(computability_rows, 1):
        cls = require_enum(latency_class_for(row, candidate_by_id.get(row["candidate_id"])), LATENCY_CLASSES, "latency_hot_path_class")
        rows.append(
            {
                "latency_hot_path_record_ref": plain_ref("LATENCY", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "latency_hot_path_class": cls,
                "latency_cost_formula": row["latency_cost_formula"],
                "hot_path_runtime_allowed": False,
                "precompute_cache_required": cls in {"HOT_PATH_SAFE_PRECOMPUTED_ONLY", "REQUIRES_CACHE_BEFORE_RUNTIME"},
                "no_llm_runtime_hot_path": True,
                "no_quantum_backend_hot_path": True,
                "downstream_pr_route": (
                    "ROUTE_TO_PR165_SCORING"
                    if row["candidate_id"]
                    else "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
                ),
                "validation_status": "PASS",
            }
        )
    return rows


def build_hot_path_cache_ledger(latency_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "hot_path_cache_preparation_ref": plain_ref("HOT_PATH_CACHE", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "latency_hot_path_class": row["latency_hot_path_class"],
            "cache_preparation_action": (
                "PRECOMPUTE_REPLAY_PAPER_CANDIDATE_CACHE"
                if row["precompute_cache_required"]
                else "CONTROL_PLANE_OR_REPLAY_PAPER_ONLY_NO_RUNTIME_CACHE"
            ),
            "validation_status": "PASS",
        }
        for index, row in enumerate(latency_rows, 1)
    ]
