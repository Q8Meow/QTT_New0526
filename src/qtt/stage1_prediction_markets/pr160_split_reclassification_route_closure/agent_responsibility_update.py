"""Agent-responsibility metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "agent_responsibility_update_id": f"PR160_AGENT_RESPONSIBILITY__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "required_actor": item["required_actor"],
            "exact_agent_id_or_null": None,
            "exact_agent_id_created_by_PR160_flag": False,
            "orphan_route_flag": False,
            "future_route": item["future_pr_route"],
        }
        for item in decisions
    ]
