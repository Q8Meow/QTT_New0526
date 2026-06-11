"""Shared row construction helpers."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .authority import authority_zero_counts
from .enums import (
    ComputabilityStatus,
    DownstreamRoute,
    NoOrphanStatus,
    SourceAuthorityClass,
    ValueAuthorityLane,
)


def stable_id(prefix: str, index: int) -> str:
    return f"{prefix}::{index:06d}"


def formula_id_from_family(formula_family: str) -> str:
    cleaned = str(formula_family or "GENERAL_REPLAY_PAPER_FORMULA_FAMILY").replace(" ", "_")
    return f"PR166_SM_FORMULA_FAMILY::{cleaned}"


def algorithm_id_from_role(role: str = "SCORE_MEMORY_REFRESH") -> str:
    return f"PR166_SM_ALGORITHM::{role}_V1"


def common_fields(
    *,
    artifact_id: str,
    row_id: str,
    upstream_artifact_refs: list[str],
    upstream_row_refs: list[str],
    downstream_artifact_refs: list[str],
    downstream_pr_refs: list[str] | None = None,
    owning_agent: str = "score_memory_refresh_agent",
    reviewer_or_challenger_agent: str = "governance_agent",
    no_orphan_status: str = NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
    value_authority_lane: str = ValueAuthorityLane.REPLAY_PAPER_CALIBRATED_VALUE_LANE.value,
    source_authority_class: str = SourceAuthorityClass.REPLAY_PAPER_RESULT_NOT_SOURCE_TRUTH.value,
    computability_status: str = ComputabilityStatus.COMPUTABLE_NOW.value,
    materialization_action_ref: str = "PR166_SM_MATERIALIZATION_ACTION::NOT_REQUIRED_COMPUTABLE_NOW",
    repair_route_ref: str = DownstreamRoute.PR165_D2.value,
    terminal_status_flag: bool = False,
    terminal_status_reason: str = c.NOT_TERMINAL_REASON,
    qku_id: str = c.NOT_APPLICABLE_ID,
    formula_id: str = c.NOT_APPLICABLE_ID,
    algorithm_id: str = c.NOT_APPLICABLE_ID,
    candidate_packet_id: str = c.NOT_APPLICABLE_ID,
    condition_fingerprint_id: str = c.NOT_APPLICABLE_ID,
    scenario_id: str = c.NOT_APPLICABLE_ID,
    combination_id: str = c.NOT_APPLICABLE_ID,
    upstream_value_refs: list[str] | None = None,
) -> dict[str, Any]:
    routes = list(downstream_pr_refs or [DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value])
    return {
        "artifact_id": artifact_id,
        "row_id": row_id,
        "created_by_pr": c.PR_ID,
        "qku_id": qku_id,
        "formula_id": formula_id,
        "algorithm_id": algorithm_id,
        "candidate_packet_id": candidate_packet_id,
        "condition_fingerprint_id": condition_fingerprint_id,
        "scenario_id": scenario_id,
        "combination_id": combination_id,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "upstream_artifact_refs": upstream_artifact_refs,
        "upstream_row_refs": upstream_row_refs,
        "upstream_value_refs": list(upstream_value_refs or []),
        "downstream_pr_refs": routes,
        "downstream_artifact_refs": downstream_artifact_refs,
        "downstream_agent_consumers": [
            "parameter_selector_agent",
            "risk_manager_agent",
            "quantum_optimizer_agent",
            "dashboard_agent",
            "governance_agent",
            "commander_agent",
        ],
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
        "computable_formula_ref": c.COMPUTABLE_FORMULA_REF,
        "materialization_action_ref": materialization_action_ref,
        "repair_route_ref": repair_route_ref,
        "score_policy_ref": c.SCORE_POLICY_REF,
        "normalization_policy_ref": c.NORMALIZATION_POLICY_REF,
        "condition_similarity_policy_ref": c.CONDITION_SIMILARITY_POLICY_REF,
        "created_at_utc": c.CREATED_AT_UTC,
        "deterministic_sort_key": row_id,
        "validation_status": c.VALIDATION_STATUS,
        **authority_zero_counts(),
    }
