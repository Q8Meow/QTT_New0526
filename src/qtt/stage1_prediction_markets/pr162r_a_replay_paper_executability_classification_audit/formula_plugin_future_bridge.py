"""PR162E formula plugin future bridge."""

from __future__ import annotations

from typing import Any


def formula_plugin_future_bridge_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_PR162E_FORMULA_PLUGIN::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "target_pr": "PR162E",
            "plugin_bridge_scope": "FORMULA_RUNTIME_PLUGIN_FUTURE_IMPLEMENTATION",
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in classifications
    ]
