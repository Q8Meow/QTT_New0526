"""Lane B: owner-policy default requests."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .master_plan_authority import owner_editability_lifecycle
from .prior_artifact_reconciliation import basis_refs, row_id_from_request
from .scoring_ranking_readiness import scoring_feature_role

POLICY_CLASS = "OWNER_APPROVED_CONSERVATIVE_INTERNAL_POLICY_DEFAULT_REPLAY_PAPER_REQUIRED"


def build(records_by_row: dict[str, Mapping[str, Any]], requests: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        row_id = row_id_from_request(request)
        row = records_by_row.get(row_id, {})
        output.append(
            {
                "lane": c.PR158Lane.LANE_B_OWNER_POLICY_DEFAULT.value,
                "request_id": request["request_id"],
                "row_id": row_id,
                "family_id": row.get("family_id"),
                "parameter_id": row.get("parameter_id"),
                "requested_value_type": request.get("requested_value_type"),
                "prior_default_available": False,
                "prior_default_source_artifact_refs": basis_refs(
                    "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json",
                    "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.registry.json",
                ),
                "deterministic_policy_default_available": True,
                "master_plan_internal_authority_available": True,
                "owner_conservative_default_required": True,
                "owner_manual_review_required": False,
                "replay_paper_required_before_live": True,
                "live_blocked_until_owner_review": True,
                "owner_dashboard_editable_flag": True,
                "owner_change_requires_policy_snapshot_flag": True,
                "scoring_feature_role_if_any": scoring_feature_role(row),
                "scoring_policy_ref_if_any": "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
                "selection_readiness_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_OWNER_RESPONSE.value,
                "completion_decision_class": c.CompletionDecisionClass.COMPLETED_FROM_OWNER_APPROVED_CONSERVATIVE_POLICY_CLASS.value,
                "response_value_or_null": POLICY_CLASS,
                "exact_next_action": "Create owner policy snapshot, then replay and paper before any live promotion review.",
                "owner_response_authority_class": c.OwnerResponseAuthorityClass.OWNER_INTERNAL_POLICY.value,
                "basis_artifact_refs": basis_refs(
                    "docs/master_plan/QTT_MasterPlan_Current.md",
                    "docs/master_plan/generated/PR157_OwnerCompletionInputRequest.packet.json",
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
        "filled_from_prior_artifact_count": 0,
        "filled_from_master_plan_internal_authority_count": 0,
        "filled_from_conservative_owner_policy_class_count": len(records),
        "numeric_range_owner_review_required_count": 0,
        "still_blocked_count": 0,
    }

