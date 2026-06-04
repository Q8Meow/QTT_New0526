"""Formula version rollback future bridge."""

from __future__ import annotations

from typing import Any


def formula_version_rollback_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_FORMULA_ROLLBACK::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "rollback_plan_future_required_flag": True,
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in classifications
    ]
