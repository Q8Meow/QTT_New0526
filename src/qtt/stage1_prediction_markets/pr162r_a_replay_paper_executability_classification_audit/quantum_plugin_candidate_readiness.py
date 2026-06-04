"""Quantum plugin candidate readiness matrix."""

from __future__ import annotations

from typing import Any


def quantum_plugin_candidate_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "quantum_plugin_candidate_ready_flag": row["candidate_type"] == "QUANTUM",
            "plugin_readiness_status": "FUTURE_QUANTUM_PLUGIN_CANDIDATE_CAPTURED"
            if row["candidate_type"] == "QUANTUM"
            else "NOT_QUANTUM_PLUGIN_SCOPE",
            "live_order_authority": False,
        }
        for row in classifications
    ]
