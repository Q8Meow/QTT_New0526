"""Agent consumability records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import agent_refs, candidate_id, candidate_type


def agent_consumability_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id(record),
            "candidate_type": candidate_type(record),
            "agent_refs": agent_refs(record),
            "agent_consumable_flag": bool(agent_refs(record)),
            "agent_consumability_status": "AGENT_CONSUMABLE_NONLIVE",
            "live_order_authority": False,
        }
        for record in records
    ]
