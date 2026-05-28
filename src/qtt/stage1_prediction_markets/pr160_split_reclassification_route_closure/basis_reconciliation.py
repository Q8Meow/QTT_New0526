"""PR160 basis reconciliation records."""

from __future__ import annotations

from typing import Any, Mapping

from .route_arbitration import selected_route


def build_basis_audit(candidate_matrix: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in candidate_matrix:
        route = selected_route(item)
        output.append(
            {
                "PR154_target_id": item.get("PR154_target_id"),
                "basis_artifact_refs": route.get("basis_artifact_refs", []),
                "basis_class": route.get("basis_class"),
                "route_confidence_class": route.get("route_confidence_class"),
                "authority_class": route.get("authority_class"),
                "basis_artifacts_present_flag": bool(route.get("basis_artifact_refs")),
                "owner_choice_packet_ref_or_null": None,
                "no_value_materialization_confirmation": True,
            }
        )
    return output
