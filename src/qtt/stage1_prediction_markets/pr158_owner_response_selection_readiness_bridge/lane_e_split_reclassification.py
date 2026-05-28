"""Lane E: PR154 split/reclassification records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .prior_artifact_reconciliation import basis_refs, target_id_from_request
from .scoring_ranking_readiness import scoring_feature_role


def build(records_by_target: dict[str, Mapping[str, Any]], requests: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        target_id = target_id_from_request(request)
        source = records_by_target.get(target_id, {})
        output.append(
            {
                "lane": c.PR158Lane.LANE_E_PR154_SPLIT_RECLASSIFICATION.value,
                "request_id": request["request_id"],
                "PR154_target_id": target_id,
                "current_source_population": request.get("source_population"),
                "current_blocker_class": c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value,
                "candidate_reclassification_class": c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value,
                "candidate_authority_class": c.OwnerResponseAuthorityClass.RECLASSIFICATION_REQUIRED.value,
                "basis_artifact_refs": basis_refs(
                    "docs/master_plan/generated/PR136RouteTriage.report.json",
                    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json",
                    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
                    source.get("completion_evidence_ref"),
                ),
                "deterministic_basis_flag": False,
                "owner_decision_required_flag": True,
                "external_fact_risk_flag": False,
                "private_doc_attestation_required_flag": False,
                "generated_derivative_possible_flag": False,
                "formula_only_possible_flag": False,
                "agent_binding_possible_flag": False,
                "quantum_classical_metadata_only_flag": "QUANTUM" in target_id,
                "scoring_feature_role_if_any": c.ScoringFeatureRole.NOT_SCORING_CONSUMABLE_YET.value,
                "selection_readiness_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_RECLASSIFICATION.value,
                "future_route": c.FutureRoute.PR160_SPLIT_RECLASSIFICATION.value,
                "exact_acceptance_criteria": "PR160 must create child targets with authority lanes, evidence scope, and validator-backed materialization routes.",
                "validator_that_will_unblock": "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
                "completion_decision_class": c.CompletionDecisionClass.PENDING_SPLIT_RECLASSIFICATION_PR160.value,
                "response_value_or_null": None,
                "exact_next_action": "Route to PR160 for deterministic split/reclassification; do not guess in PR158.",
            }
        )
    return sorted(output, key=lambda item: item["request_id"])


def aggregate(records: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "deterministically_reclassified_count": 0,
        "owner_response_completed_count": 0,
        "routed_to_PR159_count": 0,
        "routed_to_PR160_count": len(records),
        "routed_to_private_doc_attestation_count": 0,
        "routed_to_atomicrows_completion_count": 0,
        "still_blocked_count": len(records),
    }

