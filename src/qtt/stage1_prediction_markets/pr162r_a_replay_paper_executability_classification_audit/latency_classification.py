"""Latency class assignment."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def latency_class(record: dict[str, Any]) -> str:
    ctype = candidate_type(record)
    family = " ".join(
        str(record.get(key) or "")
        for key in ("algorithm_family", "formula_category", "formula_family", "parameter_family", "quantum_family")
    ).lower()
    if ctype == "QUANTUM" or any(token in family for token in ("qaoa", "vqe", "annealing", "quantum")):
        return "QUANTUM_BATCH_ONLY"
    if any(token in family for token in ("optimizer", "solver", "portfolio", "variance", "cov", "cvar", "var")):
        return "BATCH_ONLY"
    if ctype in {"PARAMETER", "DATASET"}:
        return "PRECOMPUTE_REQUIRED"
    if any(token in family for token in ("depth", "orderbook", "candlestick", "feature_builder")):
        return "PRECOMPUTE_REQUIRED"
    return "HOT_PATH_SAFE"


def latency_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id(record),
            "candidate_type": candidate_type(record),
            "latency_class": latency_class(record),
            "live_hot_path_authority_claim": False,
            "remote_quantum_hot_path_flag": False,
            "live_order_authority": False,
        }
        for record in records
    ]
