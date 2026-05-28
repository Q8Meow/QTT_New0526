"""PR161/PR162 materialization route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    eligible = {
        c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value,
        c.ReclassificationFinalRouteClass.ATOMICROWS_SOURCE_VALUE_MATERIALIZATION_ROUTE_PR161.value,
    }
    return [
        {
            "materialization_route_id": f"PR160_PR161_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "target_field_id": item["target_field_id"],
            "final_route_class": item["final_route_class"],
            "future_route": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
            "audit_route": c.FutureRoute.PR162_ATOMICROWS_FINAL_AUDIT.value,
            "required_actor": "PR161_ATOMICROWS_MATERIALIZATION_AGENT",
            "required_input_artifact": "future_PR159R_or_existing_PR159_accepted_source_packet",
            "exact_acceptance_criteria": "Accepted source packet exists before materialization; PR162 final audit passes.",
            "validator_that_will_unblock": "tools/validate_pr161_atomicrows_source_value_materialization.py",
            "source_value_materialized_by_PR160_flag": False,
            "atomicrows_record_deleted_or_shortened_flag": False,
            "atomicrows_bundle_checksum_hash_authority_created_flag": False,
        }
        for item in decisions
        if item["final_route_class"] in eligible
    ]
