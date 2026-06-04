"""Replay-ready queue helpers."""

from __future__ import annotations

from typing import Any


def is_replay_ready(classification: dict[str, Any]) -> bool:
    return "REPLAY" in str(classification.get("primary_executability_state")) and str(
        classification.get("primary_executability_state")
    ).startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE"))


def replay_ready_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "queue_id": f"PR162R_A_REPLAY_READY::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "primary_executability_state": row["primary_executability_state"],
            "partial_flag": row["primary_executability_state"].startswith("PARTIAL"),
            "replay_execution_count": 0,
            "live_order_authority": False,
        }
        for row in classifications
        if is_replay_ready(row)
    ]
