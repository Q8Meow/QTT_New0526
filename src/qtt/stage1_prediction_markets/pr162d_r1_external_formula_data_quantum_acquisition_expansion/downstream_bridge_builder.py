"""Downstream bridge report builders."""

from __future__ import annotations

from typing import Any


def downstream_bridge_records(candidates: list[dict[str, Any]], route: str) -> list[dict[str, Any]]:
    key = {
        "PR162R": "pr162r_handoff_ref",
        "PR163": "pr163_future_result_consumer_ref",
        "PR164": "pr164_future_review_ref",
        "PR165": "pr165_future_scoring_ref",
    }[route]
    return [
        {
            "bridge_id": f"PR162D_R1_{route}_BRIDGE_{index:04d}",
            "candidate_id": record["candidate_id"],
            "bridge_ref": record.get(key),
            "downstream_route": route,
            "result_packet_created_flag": False,
            "provenance_conclusion_created_flag": False,
            "result_backed_scoring_created_flag": False,
            "live_order_authority": False,
        }
        for index, record in enumerate(candidates, start=1)
    ]
