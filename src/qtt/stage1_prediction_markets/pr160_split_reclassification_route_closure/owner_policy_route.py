"""Owner-policy/internal route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    eligible = {
        c.ReclassificationFinalRouteClass.OWNER_INTERNAL_POLICY_ROUTE.value,
        c.ReclassificationFinalRouteClass.OWNER_ROUTE_METADATA_ROUTE.value,
    }
    return [
        {
            "owner_policy_route_id": f"PR160_OWNER_POLICY_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "future_route": c.FutureRoute.OWNER_POLICY_REVIEW.value,
            "owner_may_change_internal_policy_flag": True,
            "owner_change_can_create_external_fact_flag": False,
            "owner_change_requires_replay_paper_before_live_flag": True,
            "required_actor": "OWNER_POLICY_REVIEWER",
            "required_input_artifact": "owner_policy_change_receipt",
            "validator_that_will_unblock": c.PR160_VALIDATOR,
        }
        for item in decisions
        if item["final_route_class"] in eligible
    ]
