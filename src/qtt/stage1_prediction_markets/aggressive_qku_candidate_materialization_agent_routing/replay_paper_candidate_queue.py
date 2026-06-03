"""Replay/paper candidate queue helpers."""

from __future__ import annotations

from typing import Any


def replay_paper_queue_records(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "queue_id": record["route_id"].replace("AGENT-ROUTE", "REPLAY-PAPER-QUEUE"),
            "qku_id": record["qku_id"],
            "route_ref": record["route_id"],
            "replay_candidate_flag": True,
            "paper_candidate_flag": True,
            "result_packet_created_flag": False,
            "live_order_authority": False,
        }
        for record in routes
    ]
