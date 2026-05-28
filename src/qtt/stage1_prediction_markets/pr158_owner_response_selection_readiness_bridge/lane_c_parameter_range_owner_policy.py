"""Lane C: parameter-range owner-policy requests."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .master_plan_authority import owner_editability_lifecycle
from .prior_artifact_reconciliation import basis_refs, row_id_from_request
from .scoring_ranking_readiness import scoring_feature_role


def _policy_class(row: Mapping[str, Any]) -> str:
    family_id = str(row.get("family_id") or "")
    owner_editability = str(row.get("owner_editability_class") or "")
    if "RISK" in owner_editability or "risk" in family_id:
        return "CONSERVATIVE_RISK_CONTROL_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "CAPITAL" in owner_editability or "capital" in family_id or "cash" in family_id:
        return "CONSERVATIVE_CAPITAL_ALLOCATION_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "SCORING" in owner_editability or "scoring" in family_id:
        return "CONSERVATIVE_SCORING_WEIGHT_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "execution" in family_id:
        return "CONSERVATIVE_EXECUTION_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "latency" in family_id:
        return "CONSERVATIVE_LATENCY_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "error_guard" in family_id:
        return "CONSERVATIVE_ERROR_GUARD_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "QUANTUM" in owner_editability or "quantum" in family_id:
        return "CONSERVATIVE_QUANTUM_PRIORITY_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    if "optimizer" in family_id:
        return "CONSERVATIVE_OPTIMIZER_ARBITRATION_POLICY_RANGE_REPLAY_PAPER_REQUIRED"
    return "CONSERVATIVE_RISK_CONTROL_POLICY_RANGE_REPLAY_PAPER_REQUIRED"


def build(records_by_row: dict[str, Mapping[str, Any]], requests: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        row_id = row_id_from_request(request)
        row = records_by_row.get(row_id, {})
        policy = _policy_class(row)
        output.append(
            {
                "lane": c.PR158Lane.LANE_C_PARAMETER_RANGE_OWNER_POLICY.value,
                "request_id": request["request_id"],
                "row_id": row_id,
                "family_id": row.get("family_id"),
                "parameter_id": row.get("parameter_id"),
                "policy_range_family": policy,
                "requested_value_type": request.get("requested_value_type"),
                "requested_unit_or_basis": request.get("requested_unit_or_basis"),
                "requested_scale": request.get("requested_scale"),
                "prior_range_available": False,
                "prior_range_source_artifact_refs": basis_refs(
                    "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json",
                    "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.registry.json",
                    "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
                ),
                "deterministic_policy_range_available": True,
                "conservative_family_policy_class_available": True,
                "actual_numeric_range_available": False,
                "owner_manual_review_required": False,
                "replay_paper_required_before_live": True,
                "live_blocked_until_owner_review": True,
                "owner_dashboard_editable_flag": True,
                "scoring_feature_role_if_any": scoring_feature_role(row),
                "scoring_policy_ref_if_any": "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
                "optimizer_arbitration_ref_if_any": "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
                "quantum_priority_ref_if_any": "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
                "latency_path_class": c.LatencyPathClass.REPLAY_PAPER_ONLY.value,
                "selection_readiness_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_OWNER_RESPONSE.value,
                "completion_decision_class": c.CompletionDecisionClass.COMPLETED_FROM_OWNER_APPROVED_CONSERVATIVE_POLICY_CLASS.value,
                "response_value_or_null": policy,
                "exact_next_action": "Create owner policy snapshot, then replay and paper before any live promotion review.",
                "owner_response_authority_class": c.OwnerResponseAuthorityClass.OWNER_EDITABLE_PARAMETER_POLICY.value,
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
        "filled_from_conservative_family_policy_class_count": len(records),
        "numeric_range_owner_review_required_count": 0,
        "still_blocked_count": 0,
    }

