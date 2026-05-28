"""Lane A: AtomicRows agent-assignment requests."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .master_plan_authority import owner_editability_lifecycle
from .prior_artifact_reconciliation import basis_refs, row_id_from_request
from .scoring_ranking_readiness import scoring_feature_role


def build(records_by_row: dict[str, Mapping[str, Any]], requests: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        row_id = row_id_from_request(request)
        row = records_by_row.get(row_id, {})
        roles = list(row.get("responsible_agent_role_ids") or [])
        families = list(row.get("candidate_agent_family_ids") or request.get("candidate_agent_roles_or_families_if_applicable") or [])
        consumers = list(row.get("consumer_class_ids") or [])
        value = {
            "assignment_packet_class": c.AgentAssignmentStatus.ROLE_FAMILY_CONSUMER_ONLY_SUPPORTED.value,
            "row_id": row_id,
            "responsible_agent_role_ids": roles,
            "candidate_agent_family_ids": families,
            "consumer_class_ids": consumers,
            "exact_agent_id_or_null": None,
            "defer_exact_agent_id_to_PR163": True,
            "trading_permission_created": False,
        }
        output.append(
            {
                "lane": c.PR158Lane.LANE_A_AGENT_ASSIGNMENT.value,
                "request_id": request["request_id"],
                "row_id": row_id,
                "family_id": row.get("family_id"),
                "parameter_id": row.get("parameter_id"),
                "responsible_agent_role_ids": roles,
                "candidate_agent_family_ids": families,
                "consumer_class_ids": consumers,
                "exact_agent_id_supported_by_existing_artifact": False,
                "exact_agent_id_or_null": None,
                "unique_exact_agent_basis_refs": [],
                "role_only_assignment_supported": bool(roles),
                "consumer_class_assignment_supported": bool(consumers),
                "multiple_candidate_agents_ambiguous": False,
                "owner_assignment_required": False,
                "defer_exact_agent_id_to_PR163": True,
                "selection_readiness_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_EXACT_AGENT_BINDING.value,
                "scoring_feature_role_if_any": scoring_feature_role(row),
                "completion_decision_class": c.CompletionDecisionClass.COMPLETED_AS_ROLE_FAMILY_CONSUMER_RESPONSIBILITY_ONLY.value,
                "response_value_or_null": value,
                "exact_next_action": "PR163 may attach an exact agent ID only after a unique supporting artifact exists.",
                "future_route": c.FutureRoute.PR163_EXACT_AGENT_BINDING.value,
                "owner_response_authority_class": c.OwnerResponseAuthorityClass.OWNER_AGENT_RESPONSIBILITY_ASSIGNMENT.value,
                "basis_artifact_refs": basis_refs(
                    row.get("agent_binding_source_ref_or_null"),
                    "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.registry.json",
                    "docs/master_plan/QTT_MasterPlan_Current.md",
                ),
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
        "exact_agent_id_uniquely_supported_count": sum(
            1 for item in records if item["exact_agent_id_supported_by_existing_artifact"]
        ),
        "role_family_consumer_only_count": sum(
            1
            for item in records
            if item["completion_decision_class"]
            == c.CompletionDecisionClass.COMPLETED_AS_ROLE_FAMILY_CONSUMER_RESPONSIBILITY_ONLY.value
        ),
        "owner_assignment_required_count": sum(1 for item in records if item["owner_assignment_required"]),
        "exact_agent_id_deferred_to_PR163_count": sum(
            1 for item in records if item["defer_exact_agent_id_to_PR163"]
        ),
        "ambiguous_agent_candidate_count": sum(
            1 for item in records if item["multiple_candidate_agents_ambiguous"]
        ),
        "blocked_no_responsible_route_count": 0,
    }

