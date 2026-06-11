"""Shared row construction helpers for PR165-D2."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .authority import authority_zero_counts
from .enums import (
    ComputabilityStatus,
    ConnectorDependencyClass,
    DownstreamRoute,
    NoOrphanStatus,
    SourceAuthorityClass,
    ValueAuthorityLane,
    VenueSemanticDependencyClass,
)


def stable_id(prefix: str, index: int) -> str:
    return f"{prefix}::{index:06d}"


def common_fields(
    *,
    artifact_id: str,
    row_id: str,
    upstream_artifact_refs: list[str],
    upstream_row_refs: list[str],
    upstream_value_refs: list[str] | None = None,
    downstream_pr_refs: list[str] | None = None,
    downstream_artifact_refs: list[str] | None = None,
    downstream_agent_consumers: list[str] | None = None,
    owning_agent: str = "parameter_selector_agent",
    reviewer_or_challenger_agent: str = "governance_agent",
    no_orphan_status: str = NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
    value_authority_lane: str = ValueAuthorityLane.REPLAY_PAPER_SELECTION_CANDIDATE_LANE.value,
    source_authority_class: str = SourceAuthorityClass.REPLAY_PAPER_RESULT_NOT_SOURCE_TRUTH.value,
    computability_status: str = ComputabilityStatus.COMPUTABLE_AFTER_EXACT_MATERIALIZATION_ACTION.value,
    selection_state: str = "TERMINAL_BY_NATURE_WITH_REASON",
    materialization_action_ref: str = "PR165_D2_MATERIALIZATION_ACTION::NOT_REQUIRED_FOR_THIS_ROW_TERMINAL_BY_NATURE",
    repair_route_ref: str = "PR165_D2_REPAIR_ROUTE::NOT_REQUIRED_FOR_THIS_ROW_TERMINAL_BY_NATURE",
    terminal_status_flag: bool = False,
    terminal_status_reason: str = c.NOT_TERMINAL_REASON,
    qku_id: str = c.NOT_APPLICABLE_ID,
    formula_id: str = c.NOT_APPLICABLE_ID,
    algorithm_id: str = c.NOT_APPLICABLE_ID,
    candidate_packet_id: str = c.NOT_APPLICABLE_ID,
    condition_fingerprint_id: str = c.NOT_APPLICABLE_ID,
    scenario_group_id: str = c.NOT_APPLICABLE_ID,
    combination_id: str = c.NOT_APPLICABLE_ID,
    connector_dependency_class: str = ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value,
    venue_semantic_dependency_class: str = VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value,
    future_connector_pr_refs: list[str] | None = None,
    future_venue_readiness_route: str = "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
) -> dict[str, Any]:
    downstream_pr_refs = list(
        downstream_pr_refs or [DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value]
    )
    downstream_artifact_refs = list(downstream_artifact_refs or [c.MANIFEST_REF])
    future_connector_pr_refs = list(future_connector_pr_refs or ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"])
    return {
        "artifact_id": artifact_id,
        "row_id": row_id,
        "created_by_pr": c.PR_ID,
        "qku_id": qku_id,
        "formula_id": formula_id,
        "algorithm_id": algorithm_id,
        "candidate_packet_id": candidate_packet_id,
        "condition_fingerprint_id": condition_fingerprint_id,
        "scenario_group_id": scenario_group_id,
        "combination_id": combination_id,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "upstream_artifact_refs": upstream_artifact_refs,
        "upstream_row_refs": upstream_row_refs,
        "upstream_value_refs": list(upstream_value_refs or []),
        "downstream_pr_refs": downstream_pr_refs,
        "downstream_artifact_refs": downstream_artifact_refs,
        "downstream_agent_consumers": list(
            downstream_agent_consumers
            or [
                "parameter_selector_agent",
                "risk_manager_agent",
                "quantum_optimizer_agent",
                "dashboard_agent",
                "governance_agent",
                "commander_agent",
            ]
        ),
        "owning_agent": owning_agent,
        "reviewer_or_challenger_agent": reviewer_or_challenger_agent,
        "validator_ref": c.VALIDATOR_REF,
        "manifest_ref": c.MANIFEST_REF,
        "schema_ref": "",
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": no_orphan_status,
        "terminal_status_flag": terminal_status_flag,
        "terminal_status_reason": terminal_status_reason,
        "value_authority_lane": value_authority_lane,
        "source_authority_class": source_authority_class,
        "computability_status": computability_status,
        "selection_state": selection_state,
        "materialization_action_ref": materialization_action_ref,
        "repair_route_ref": repair_route_ref,
        "score_policy_ref": c.SCORE_POLICY_REF,
        "normalization_policy_ref": c.NORMALIZATION_POLICY_REF,
        "condition_memory_policy_ref": c.CONDITION_MEMORY_POLICY_REF,
        "connector_readiness_policy_ref": c.CONNECTOR_READINESS_POLICY_REF,
        "created_at_utc": c.CREATED_AT_UTC,
        "deterministic_sort_key": row_id,
        "connector_dependency_class": connector_dependency_class,
        "venue_semantic_dependency_class": venue_semantic_dependency_class,
        "future_connector_pr_refs": future_connector_pr_refs,
        "future_venue_readiness_route": future_venue_readiness_route,
        "connector_binding_allowed_in_this_pr": False,
        "private_state_fetch_allowed_in_this_pr": False,
        "runtime_cash_receipt_allowed_in_this_pr": False,
        "source_truth_acceptance_allowed_in_this_pr": False,
        "validation_status": c.VALIDATION_STATUS,
        **authority_zero_counts(),
    }
