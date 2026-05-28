"""Route-collision audit for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build_route_collision_audit(candidate_matrix: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in candidate_matrix:
        routes = item.get("candidate_routes") if isinstance(item.get("candidate_routes"), list) else []
        records.append(
            {
                "PR154_target_id": item.get("PR154_target_id"),
                "plausible_route_classes": [
                    route.get("candidate_route_class")
                    for route in routes
                    if isinstance(route, Mapping)
                ],
                "plausible_route_count": len(routes),
                "route_collision_flag": len(routes) > 1,
                "collision_resolved_by_arbitration_flag": len(routes) <= 1,
                "owner_choice_packet_required_flag": False,
                "owner_choice_question_id_or_null": None,
                "unresolved_collision_blocked_flag": False,
            }
        )
    return records
