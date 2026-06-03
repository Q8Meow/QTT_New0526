"""Replay/paper queue for every external candidate."""

from __future__ import annotations

from typing import Any


def replay_paper_external_candidate_queue_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "queue_id": f"PR162D_R1_REPLAY_PAPER_QUEUE_{index:04d}",
            "candidate_id": record["candidate_id"],
            "replay_paper_route_refs": record.get("replay_paper_route_refs", []),
            "replay_route": "REPLAY_ENGINE_INPUT_PREP",
            "paper_route": "PAPER_ENGINE_INPUT_PREP",
            "result_packet_created_flag": False,
            "profit_evidence_claim_flag": False,
            "live_order_authority": False,
        }
        for index, record in enumerate(candidates, start=1)
    ]
