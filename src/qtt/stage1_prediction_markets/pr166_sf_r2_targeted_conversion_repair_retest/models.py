"""Shared row model helpers for PR166-SF-R2."""

from __future__ import annotations

import hashlib
from typing import Any

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .enums import AgentId, NoOrphanStatus


def stable_id(prefix: str, *parts: object) -> str:
    raw = "::".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
    return f"{prefix}::{digest}"


def common_fields(
    *,
    report_filename: str,
    row_id: str,
    index: int,
    source: dict[str, Any] | None = None,
    upstream_artifact_refs: list[str] | None = None,
    upstream_row_refs: list[str] | None = None,
    downstream_pr_refs: list[str] | None = None,
    downstream_artifact_refs: list[str] | None = None,
    owning_agent: str = AgentId.RISK_MANAGER.value,
    reviewer_agent: str = AgentId.GOVERNANCE.value,
    no_orphan_status: str = NoOrphanStatus.REPAIR.value,
) -> dict[str, Any]:
    src = source or {}
    candidate = str(src.get("candidate_packet_id") or c.NOT_APPLICABLE_ID)
    route_refs = downstream_pr_refs or ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"]
    artifact_refs = downstream_artifact_refs or [report_filename]
    return {
        "artifact_id": report_filename.removesuffix(".report.json"),
        "row_id": row_id,
        "created_at_utc": c.CREATED_AT_UTC,
        "created_by_pr": c.PR_ID,
        "roadmap_pr_id": c.PR_ID,
        "candidate_packet_id": candidate,
        "qku_id": src.get("qku_id", c.NOT_APPLICABLE_ID),
        "formula_id": src.get("formula_id", c.NOT_APPLICABLE_ID),
        "algorithm_id": src.get("algorithm_id", c.NOT_APPLICABLE_ID),
        "parameter_stack_id": src.get("parameter_stack_id", c.NOT_APPLICABLE_ID),
        "condition_fingerprint_id": src.get("condition_fingerprint_id", c.NOT_APPLICABLE_ID),
        "scenario_group_id": src.get("scenario_group_id", c.NOT_APPLICABLE_ID),
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "upstream_artifact_refs": upstream_artifact_refs or ["PR166_SM2_AllNegConvPlan.report.json"],
        "upstream_row_refs": upstream_row_refs or [str(src.get("row_id") or f"UPSTREAM::{index:05d}")],
        "upstream_value_refs": [
            f"{candidate}::replay_paper_net_edge_after_costs",
            f"{candidate}::break_even_gap",
        ],
        "source_roadmap_pr_refs": list(c.UPSTREAM_PR_REFS),
        "source_artifact_refs": upstream_artifact_refs or ["PR166_SM2_AllNegConvPlan.report.json"],
        "source_row_refs": upstream_row_refs or [str(src.get("row_id") or f"UPSTREAM::{index:05d}")],
        "input_shard_refs": src.get("input_shard_refs") or ["ROOT_OR_DECLARED_SHARD_CONSUMED"],
        "pr166_sm2_conversion_plan_ref": src.get("convertible_negative_ref", src.get("row_id", c.NOT_APPLICABLE_ID)),
        "pr166_sm2_repair_priority_ref": src.get("repair_priority_ref", src.get("convertible_negative_ref", c.NOT_APPLICABLE_ID)),
        "pr166_sm2_break_even_gap_ref": src.get("break_even_gap_ref", c.NOT_APPLICABLE_ID),
        "pr166_s2_retest_result_ref": src.get("original_pr166_s2_row_refs", src.get("row_id", c.NOT_APPLICABLE_ID)),
        "downstream_pr_refs": route_refs,
        "downstream_artifact_refs": artifact_refs,
        "downstream_agent_consumers": [owning_agent, reviewer_agent],
        "owning_agent": owning_agent,
        "reviewer_or_challenger_agent": reviewer_agent,
        "validator_ref": c.VALIDATOR_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[report_filename],
        "manifest_ref": c.MANIFEST_REF,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "no_orphan_status": no_orphan_status,
        "terminal_status_flag": False,
        "terminal_status_reason": c.NOT_TERMINAL_REASON,
        "deterministic_sort_key": f"{report_filename}::{index:05d}::{candidate}",
        "connector_dependency_class": "CONNECTOR_REFERENCE_ONLY_NO_BINDING",
        "venue_semantic_dependency_class": "VENUE_REFERENCE_ONLY_NO_SEMANTIC_BINDING",
        "future_connector_pr_refs": list(c.FUTURE_CONNECTOR_PR_REFS),
        "future_venue_readiness_route": "PR174_PR181_REFERENCE_ONLY_AUTHORITY_FLAGS_FALSE",
        "connector_binding_allowed_in_this_pr": False,
        "connector_semantic_binding_allowed_in_this_pr": False,
        "venue_semantic_binding_allowed_in_this_pr": False,
        "live_order_authority_allowed_in_this_pr": False,
        "live_order_authority_allowed": False,
        "profit_evidence_allowed_in_this_pr": False,
        "private_state_fetch_allowed_in_this_pr": False,
        "runtime_cash_receipt_allowed_in_this_pr": False,
        "source_truth_acceptance_allowed_in_this_pr": False,
        "quantum_backend_execution_allowed_in_this_pr": False,
        "quantum_advantage_claim_allowed_in_this_pr": False,
        "not_profit_evidence": True,
        **authority_zero_counts(),
    }
