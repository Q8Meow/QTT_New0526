"""PR163 exact-agent binding route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "agent_binding_route_id": f"PR160_PR163_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "future_route": c.FutureRoute.PR163_EXACT_AGENT_BINDING.value,
            "required_actor": "PR163_EXACT_AGENT_BINDING_AGENT",
            "required_input_artifact": "future_exact_agent_binding_map",
            "validator_that_will_unblock": "tools/validate_pr163_exact_agent_binding.py",
            "exact_agent_id_created_by_PR160_flag": False,
        }
        for item in decisions
        if item["final_route_class"]
        == c.ReclassificationFinalRouteClass.EXACT_AGENT_BINDING_ROUTE_PR163.value
    ]
