"""Partial replay/paper candidate helpers."""

from __future__ import annotations

from typing import Any


def partial_candidate_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "queue_id": f"PR162R_A_PARTIAL::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "primary_executability_state": row["primary_executability_state"],
            "secondary_tags": row["secondary_tags"],
            "candidate_or_provisional_flag": True,
            "live_ready_flag": False,
            "order_ready_flag": False,
            "live_order_authority": False,
        }
        for row in classifications
        if str(row.get("primary_executability_state", "")).startswith("PARTIAL_EXECUTABLE")
    ]
