"""Agent formula scout future bridge."""

from __future__ import annotations

from typing import Any


def agent_formula_scout_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_AGENT_FORMULA_SCOUT::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "agent_formula_scout_future_flag": True,
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in classifications
    ]
