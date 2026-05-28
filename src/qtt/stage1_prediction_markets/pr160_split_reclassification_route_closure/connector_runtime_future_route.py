"""Connector/runtime future route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    eligible = {
        c.ReclassificationFinalRouteClass.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value,
        c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value,
    }
    return [
        {
            "connector_runtime_route_id": f"PR160_CONNECTOR_RUNTIME_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "future_route": item["future_pr_route"],
            "required_actor": item["required_actor"],
            "required_input_artifact": item["required_input_artifact"],
            "validator_that_will_unblock": item["validator_that_will_unblock"],
            "connector_semantic_binding_created_by_PR160_flag": False,
            "runtime_receipt_created_by_PR160_flag": False,
            "private_state_fetch_created_by_PR160_flag": False,
            "live_order_authority_created_by_PR160_flag": False,
        }
        for item in decisions
        if item["final_route_class"] in eligible
    ]
