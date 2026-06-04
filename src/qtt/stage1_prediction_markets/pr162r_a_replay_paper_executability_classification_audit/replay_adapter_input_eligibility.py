"""Replay adapter input eligibility records."""

from __future__ import annotations

from typing import Any


def replay_adapter_input_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in classifications:
        state = str(row.get("primary_executability_state"))
        eligible = state.startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE")) and "REPLAY" in state
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "replay_adapter_input_eligible_flag": eligible,
                "primary_executability_state": state,
                "replay_execution_count": 0,
                "result_packet_created_flag": False,
                "live_order_authority": False,
            }
        )
    return rows
