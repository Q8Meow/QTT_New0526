"""Cross-lane S AtomicRows selection-readiness overlay."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .scoring_ranking_readiness import scoring_feature_role
from .trade_context_selection_readiness import (
    CANDIDATE_STACK_GENERATION_REFS,
    SELECTED_STACK_HANDOFF_REFS,
    SELECTION_UNIVERSE_REFS,
    TRADE_CONTEXT_APPLICABILITY_REFS,
)


def _request_id(record: Mapping[str, Any]) -> str | None:
    blocker = str(record.get("blocker_class") or "")
    row_id = str(record.get("row_id_or_row_ref") or "")
    if blocker == "OWNER_INPUT_REQUIRED" or record.get("source_requirement_class") in {
        "OWNER_POLICY_DEFAULT",
        "PARAMETER_RANGE_OWNER_POLICY",
    }:
        return f"PR157_ATOMICROWS_OWNER_INPUT_REQUEST__{row_id}"
    if blocker == "OWNER_AGENT_ASSIGNMENT_REQUIRED":
        return f"PR157_ATOMICROWS_AGENT_ASSIGNMENT_REQUEST__{row_id}"
    return None


def _owner_status(record: Mapping[str, Any], completed_request_ids: set[str]) -> str:
    request_id = _request_id(record)
    if request_id and request_id in completed_request_ids:
        if str(record.get("source_requirement_class")) == "AGENT_BINDING_REQUIRED":
            return c.CompletionDecisionClass.COMPLETED_AS_ROLE_FAMILY_CONSUMER_RESPONSIBILITY_ONLY.value
        return c.CompletionDecisionClass.COMPLETED_FROM_OWNER_APPROVED_CONSERVATIVE_POLICY_CLASS.value
    if request_id:
        return c.CompletionDecisionClass.PENDING_OWNER_REVIEW.value
    if record.get("public_source_required_flag") is True:
        return c.CompletionDecisionClass.PENDING_PUBLIC_SOURCE_PR159.value
    return c.CompletionDecisionClass.COMPLETED_AS_SELECTION_READINESS_METADATA_ONLY.value


def _selection_status(record: Mapping[str, Any], completed_request_ids: set[str]) -> str:
    source = str(record.get("source_requirement_class") or "")
    request_id = _request_id(record)
    if source == "AGENT_BINDING_REQUIRED":
        return c.SelectionReadinessStatus.SELECTION_READY_AFTER_EXACT_AGENT_BINDING.value
    if request_id and request_id in completed_request_ids:
        return c.SelectionReadinessStatus.SELECTION_READY_AFTER_OWNER_RESPONSE.value
    if record.get("public_source_required_flag") is True:
        return c.SelectionReadinessStatus.SELECTION_READY_AFTER_SOURCE_EVIDENCE.value
    return c.SelectionReadinessStatus.SELECTION_READY_METADATA_ONLY.value


def _blocker(record: Mapping[str, Any], completed_request_ids: set[str]) -> str:
    source = str(record.get("source_requirement_class") or "")
    if source == "AGENT_BINDING_REQUIRED":
        return c.BlockerClass.EXACT_AGENT_ID_REQUIRED.value
    if record.get("public_source_required_flag") is True:
        return c.BlockerClass.PUBLIC_SOURCE_REQUIRED.value
    request_id = _request_id(record)
    if request_id and request_id not in completed_request_ids:
        return c.BlockerClass.OWNER_REVIEW_REQUIRED.value
    return c.BlockerClass.NONE.value


def _future_route(record: Mapping[str, Any], blocker: str) -> str:
    if blocker == c.BlockerClass.EXACT_AGENT_ID_REQUIRED.value:
        return c.FutureRoute.PR163_EXACT_AGENT_BINDING.value
    if blocker == c.BlockerClass.PUBLIC_SOURCE_REQUIRED.value:
        return c.FutureRoute.PR159_PUBLIC_SOURCE_RETRY.value
    if blocker == c.BlockerClass.OWNER_REVIEW_REQUIRED.value:
        return c.FutureRoute.OWNER_REVIEW_AFTER_FUTURE_GATES.value
    if record.get("optimizer_future_candidate_flag") is True:
        return c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value
    return c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value


def _latency_path(blocker: str, role: str) -> str:
    if blocker != c.BlockerClass.NONE.value:
        return c.LatencyPathClass.BLOCKED_FROM_LIVE_PATH.value
    if role in {
        c.ScoringFeatureRole.REPLAY_PAPER_EVALUATION_FEATURE.value,
        c.ScoringFeatureRole.RISK_FILTER.value,
        c.ScoringFeatureRole.CAPITAL_FILTER.value,
    }:
        return c.LatencyPathClass.REPLAY_PAPER_ONLY.value
    return c.LatencyPathClass.LOW_LATENCY_PRECOMPUTED_INDEX_ELIGIBLE.value


def build(records: list[Mapping[str, Any]], completed_request_ids: set[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        row_id = str(record.get("row_id_or_row_ref") or "")
        role = scoring_feature_role(record)
        blocker = _blocker(record, completed_request_ids)
        latency_path = _latency_path(blocker, role)
        compatibility = list(record.get("quantum_classical_compatibility") or [])
        output.append(
            {
                "row_id": row_id,
                "family_id": record.get("family_id"),
                "parameter_id": record.get("parameter_id"),
                "formula_algorithm_edge_alpha_id_or_null": record.get("formula_algorithm_edge_alpha_id_or_null"),
                "source_requirement_class": record.get("source_requirement_class"),
                "completion_status_from_PR157_or_PR158": _selection_status(record, completed_request_ids),
                "owner_response_request_id_or_null": _request_id(record),
                "owner_response_status": _owner_status(record, completed_request_ids),
                "responsible_agent_role_ids": list(record.get("responsible_agent_role_ids") or []),
                "candidate_agent_family_ids": list(record.get("candidate_agent_family_ids") or []),
                "consumer_class_ids": list(record.get("consumer_class_ids") or []),
                "exact_agent_id_or_null": None,
                "agent_assignment_status": (
                    c.AgentAssignmentStatus.EXACT_AGENT_ID_DEFERRED_TO_PR163.value
                    if str(record.get("source_requirement_class")) == "AGENT_BINDING_REQUIRED"
                    else c.AgentAssignmentStatus.ROLE_FAMILY_CONSUMER_ONLY_SUPPORTED.value
                ),
                "scoring_feature_role": role,
                "scoring_policy_ref_or_null": "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
                "scoring_weight_owner_editable_flag": record.get("owner_editability_class") == c.OwnerEditabilityClass.OWNER_EDITABLE_SCORING_WEIGHT.value,
                "scoring_weight_source_class": "OWNER_POLICY_CLASS" if record.get("owner_dashboard_editable_flag") else "DERIVED_FROM_ACCEPTED_INPUTS_ONLY",
                "scoring_weight_value_or_policy_class_or_null": (
                    "OWNER_POLICY_CLASS_ONLY_NO_SCORING_EXECUTION"
                    if role
                    in {
                        c.ScoringFeatureRole.SCORE_WEIGHT.value,
                        c.ScoringFeatureRole.QUANTUM_PRIORITY_FEATURE.value,
                    }
                    else None
                ),
                "scoring_constraint_refs": ["docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"],
                "ranking_gate_ref_or_null": "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json",
                "trade_context_applicability_refs": TRADE_CONTEXT_APPLICABILITY_REFS,
                "selection_universe_refs": SELECTION_UNIVERSE_REFS,
                "candidate_stack_generation_refs": CANDIDATE_STACK_GENERATION_REFS,
                "selected_stack_handoff_refs_if_any": SELECTED_STACK_HANDOFF_REFS,
                "market_scope": "PREDICTION_MARKETS_GENERAL",
                "platform_scope": "PREDICTION_MARKETS_GENERAL",
                "venue_scope": "PREDICTION_MARKETS_GENERAL",
                "strategy_scope": "STATIC_SELECTION_READINESS_METADATA_ONLY",
                "edge_type_scope": role,
                "latency_sensitivity_class": latency_path,
                "latency_path_class": latency_path,
                "risk_mode_scope": "FUTURE_REPLAY_PAPER_AND_OWNER_REVIEW_REQUIRED",
                "capital_intensity_class": "POLICY_CLASS_ONLY_NO_NUMERIC_ALLOCATION",
                "execution_sensitivity_class": "NO_LIVE_EXECUTION_AUTHORITY",
                "replay_paper_required_before_live_flag": True,
                "owner_review_required_before_live_flag": True,
                "quantum_classical_compatibility": compatibility,
                "quantum_priority_policy_ref_or_null": "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
                "optimizer_arbitration_ref_or_null": "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
                "quantum_backend_execution_allowed_flag": False,
                "optimizer_execution_allowed_flag": False,
                "scoring_execution_allowed_flag": False,
                "live_order_authority_allowed_flag": False,
                "low_latency_precomputed_index_eligible_flag": (
                    latency_path == c.LatencyPathClass.LOW_LATENCY_PRECOMPUTED_INDEX_ELIGIBLE.value
                ),
                "future_research_addition_status": c.FutureResearchAdditionStatus.FUTURE_RESEARCH_ADDITION_COMPATIBLE.value,
                "future_route": _future_route(record, blocker),
                "blocker_class": blocker,
                "AtomicRows_semantic_contract_ref": record.get("AtomicRows_semantic_contract_ref"),
                "AtomicRows_reconciliation_ref": record.get("AtomicRows_reconciliation_ref"),
                "exact_next_action": (
                    "Ready as static metadata for future PR164/PR165 gates."
                    if blocker == c.BlockerClass.NONE.value
                    else "Complete the typed future route before scoring, ranking, selection, replay, paper, or live use."
                ),
            }
        )
    return sorted(output, key=lambda item: item["row_id"])


def aggregate(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    statuses = [str(item["completion_status_from_PR157_or_PR158"]) for item in records]
    roles = [str(item["scoring_feature_role"]) for item in records]
    latency = [str(item["latency_path_class"]) for item in records]
    compatibility_lists = [list(item.get("quantum_classical_compatibility") or []) for item in records]
    trade_context_counts = {
        "QTTTradeContextPacket": sum(
            1
            for item in records
            if "docs/master_plan/generated/QTTTradeContextPacket.report.json"
            in item["trade_context_applicability_refs"]
        ),
        "AtomicRowsTradeContextSelectionUniverseRoutingGate": sum(
            1
            for item in records
            if "docs/master_plan/generated/AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
            in item["trade_context_applicability_refs"]
        ),
    }
    return {
        "atomicrows_selection_readiness_total_count": len(records),
        "selection_ready_metadata_only_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_METADATA_ONLY.value),
        "selection_ready_after_owner_response_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_AFTER_OWNER_RESPONSE.value),
        "selection_ready_after_source_evidence_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_AFTER_SOURCE_EVIDENCE.value),
        "selection_ready_after_private_doc_attestation_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_AFTER_PRIVATE_DOC_ATTESTATION.value),
        "selection_ready_after_exact_agent_binding_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_AFTER_EXACT_AGENT_BINDING.value),
        "selection_ready_after_reclassification_count": statuses.count(c.SelectionReadinessStatus.SELECTION_READY_AFTER_RECLASSIFICATION.value),
        "not_selection_ready_blocked_count": statuses.count(c.SelectionReadinessStatus.NOT_SELECTION_READY_BLOCKED.value),
        "not_selection_applicable_count": statuses.count(c.SelectionReadinessStatus.NOT_SELECTION_APPLICABLE.value),
        "scoring_feature_role_counts": dict(sorted(__import__("collections").Counter(roles).items())),
        "trade_context_applicability_counts": trade_context_counts,
        "latency_path_class_counts": dict(sorted(__import__("collections").Counter(latency).items())),
        "quantum_inspired_candidate_count": sum(
            1
            for items in compatibility_lists
            if c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value in items
        ),
        "true_quantum_candidate_count": sum(
            1 for items in compatibility_lists if c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value in items
        ),
        "hybrid_candidate_count": sum(
            1
            for items in compatibility_lists
            if c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value in items
        ),
        "classical_only_baseline_count": sum(
            1
            for items in compatibility_lists
            if c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value in items
        ),
        "optimizer_arbitration_metadata_count": sum(1 for item in records if item["optimizer_arbitration_ref_or_null"]),
        "low_latency_precomputed_index_eligible_count": sum(
            1 for item in records if item["low_latency_precomputed_index_eligible_flag"]
        ),
        "live_order_authority_allowed_count": sum(
            1 for item in records if item["live_order_authority_allowed_flag"]
        ),
        "scoring_execution_allowed_count": sum(1 for item in records if item["scoring_execution_allowed_flag"]),
        "optimizer_execution_allowed_count": sum(1 for item in records if item["optimizer_execution_allowed_flag"]),
        "quantum_backend_execution_allowed_count": sum(
            1 for item in records if item["quantum_backend_execution_allowed_flag"]
        ),
    }
