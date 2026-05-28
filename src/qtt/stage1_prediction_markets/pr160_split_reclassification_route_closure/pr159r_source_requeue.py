"""PR159R source-target requeue records for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requeue_id": f"PR160_PR159R_REQUEUE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "target_field_id": item["target_field_id"],
            "requested_value_name": item["requested_value_name"],
            "source_requirement_route": c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value,
            "future_route": c.FutureRoute.PR159R_EXACT_SOURCE_LOCATOR_VALUE_UNIT_CAPTURE.value,
            "required_actor": item["required_actor"],
            "required_input_artifact": "future_PR159R_accepted_source_packet",
            "exact_steps_to_fill": [
                "Capture an official source locator for the exact target field.",
                "Extract value, unit, scale, freshness, and conflict status in PR159R.",
                "Accept only through PR159R validation before PR161/PR162 materialization.",
            ],
            "exact_acceptance_criteria": "PR159R accepted packet matches PR154 target_id and target_field_id exactly.",
            "validator_that_will_unblock": c.PR159_VALIDATOR,
            "accepted_source_packet_created_by_PR160_flag": False,
            "accepted_value_created_by_PR160_flag": False,
            "target_field_acceptance_ledger_created_by_PR160_flag": False,
            "can_qtt_use_in_live_flag": False,
        }
        for item in decisions
        if item["final_route_class"]
        == c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value
    ]
