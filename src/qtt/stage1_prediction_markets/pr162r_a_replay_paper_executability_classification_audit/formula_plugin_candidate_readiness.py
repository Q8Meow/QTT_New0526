"""Formula plugin candidate readiness matrix."""

from __future__ import annotations

from typing import Any


def formula_plugin_candidate_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "formula_plugin_candidate_ready_flag": row["candidate_type"] in {"FORMULA", "ALGORITHM", "PARAMETER"},
            "plugin_readiness_status": "FUTURE_PLUGIN_CANDIDATE_CAPTURED",
            "live_order_authority": False,
        }
        for row in classifications
    ]
