"""Future downstream bridge builders."""

from __future__ import annotations

from typing import Any


def downstream_bridge_records(classifications: list[dict[str, Any]], target_pr: str) -> list[dict[str, Any]]:
    return [
        {
            "bridge_id": f"PR162R_A_{target_pr}_BRIDGE::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "target_pr": target_pr,
            "primary_executability_state": row["primary_executability_state"],
            "future_scope_only_flag": True,
            "result_packet_created_flag": False,
            "profit_evidence_claim_flag": False,
            "live_order_authority": False,
        }
        for row in classifications
    ]
