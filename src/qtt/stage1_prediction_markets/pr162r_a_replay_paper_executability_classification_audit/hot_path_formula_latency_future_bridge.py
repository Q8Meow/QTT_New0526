"""Hot-path formula latency future bridge."""

from __future__ import annotations

from typing import Any


def hot_path_latency_records(latency_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_HOT_PATH_LATENCY::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "latency_class": row["latency_class"],
            "live_hot_path_approved_now_flag": False,
            "remote_quantum_hot_path_flag": row["remote_quantum_hot_path_flag"],
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for row in latency_records
    ]
