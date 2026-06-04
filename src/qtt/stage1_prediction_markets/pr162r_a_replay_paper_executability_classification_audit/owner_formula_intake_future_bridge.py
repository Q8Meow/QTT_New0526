"""Owner formula intake future bridge."""

from __future__ import annotations

from typing import Any


def owner_formula_intake_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_OWNER_FORMULA_INTAKE::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "owner_review_optional_flag": "OWNER_REVIEW_OPTIONAL" in row.get("secondary_tags", []),
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in classifications
    ]
