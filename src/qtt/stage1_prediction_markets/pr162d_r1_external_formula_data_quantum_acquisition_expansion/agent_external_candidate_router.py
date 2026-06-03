"""Agent routing matrix for every external candidate."""

from __future__ import annotations

from typing import Any


def agent_external_candidate_route_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "agent_route_id": f"PR162D_R1_AGENT_ROUTE_{index:04d}",
            "candidate_id": record["candidate_id"],
            "agent_refs": record.get("agent_refs") or record.get("agent_route_refs", []),
            "agent_route_refs": record.get("agent_route_refs") or record.get("agent_refs", []),
            "route_status": "CANDIDATE_REPLAY_PAPER_ROUTED_NO_LIVE_AUTHORITY",
            "order_submission_allowed_flag": False,
            "live_order_authority": False,
        }
        for index, record in enumerate(candidates, start=1)
    ]
