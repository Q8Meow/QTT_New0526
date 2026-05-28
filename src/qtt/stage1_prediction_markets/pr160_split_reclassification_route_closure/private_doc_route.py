"""Private-document attestation route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "private_doc_route_id": f"PR160_PRIVATE_DOC_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "future_route": c.FutureRoute.OWNER_PRIVATE_DOC_ATTESTATION.value,
            "required_actor": "OWNER_PRIVATE_DOC_ATTESTATION_REVIEWER",
            "required_input_artifact": "owner_private_doc_attestation_response",
            "validator_that_will_unblock": c.PR160_VALIDATOR,
            "private_doc_attestation_created_by_PR160_flag": False,
            "raw_secret_capture_forbidden_flag": True,
        }
        for item in decisions
        if item["final_route_class"]
        == c.ReclassificationFinalRouteClass.PRIVATE_DOC_ATTESTATION_ROUTE.value
    ]
