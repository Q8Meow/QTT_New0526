"""Runtime formula allowlist future bridge."""

from __future__ import annotations

from typing import Any


def runtime_formula_allowlist_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_RUNTIME_ALLOWLIST::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "runtime_allowlist_future_candidate_flag": row["primary_executability_state"].startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE")),
            "live_runtime_allowlisted_now_flag": False,
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in classifications
    ]
