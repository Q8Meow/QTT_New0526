"""Lane D: PR154 owner-route records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .master_plan_authority import owner_editability_lifecycle
from .prior_artifact_reconciliation import basis_refs, target_id_from_request


def build(records_by_target: dict[str, Mapping[str, Any]], requests: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        target_id = target_id_from_request(request)
        source = records_by_target.get(target_id, {})
        roles = list(request.get("candidate_agent_roles_or_families_if_applicable") or source.get("candidate_agent_family_ids") or [])
        value = {
            "route_packet_class": "PR154_INTERNAL_OWNER_ROUTE_METADATA_ONLY",
            "target_id": target_id,
            "route_family": roles[0] if roles else None,
            "candidate_agent_roles_or_families": roles,
            "external_fact_created": False,
            "live_authority_created": False,
        }
        output.append(
            {
                "lane": c.PR158Lane.LANE_D_PR154_OWNER_ROUTE.value,
                "request_id": request["request_id"],
                "PR154_target_id": target_id,
                "route_family": roles[0] if roles else None,
                "candidate_agent_roles_or_families": roles,
                "prior_route_artifact_available": True,
                "prior_route_artifact_refs": basis_refs(
                    "docs/master_plan/generated/PR136RouteTriage.report.json",
                    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
                    source.get("downstream_pr155_ref_or_null"),
                    source.get("downstream_pr156_binding_ref_or_null"),
                ),
                "deterministic_owner_route_packet_available": True,
                "owner_manual_review_required": False,
                "owner_route_response_value": value,
                "replay_paper_required_before_live": True,
                "live_blocked_until_owner_review": True,
                "scoring_policy_ref_if_any": "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
                "selection_readiness_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_OWNER_RESPONSE.value,
                "completion_decision_class": c.CompletionDecisionClass.COMPLETED_AS_INTERNAL_ROUTE_METADATA.value,
                "exact_next_action": "Preserve route metadata as control-plane input; replay and paper remain required before live.",
                "response_value_or_null": value,
                "owner_response_authority_class": c.OwnerResponseAuthorityClass.OWNER_ROUTE_DECISION.value,
                **owner_editability_lifecycle(
                    str(request.get("requested_value_type") or ""),
                    str(request.get("requested_unit_or_basis") or ""),
                    str(request.get("requested_scale") or ""),
                ),
            }
        )
    return sorted(output, key=lambda item: item["request_id"])


def aggregate(records: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "filled_from_prior_artifact_count": 0,
        "filled_from_master_plan_internal_authority_count": 0,
        "filled_from_owner_route_policy_count": len(records),
        "manual_review_required_count": 0,
        "still_blocked_count": 0,
    }

