"""Population routing for PR155-ready and PR154/PR155-blocked records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .agent_binding import binding_for_pr155_record
from .classical_quantum_applicability import applicability_for_pr155_record
from .future_routing import population_optimizer_hint
from .io import as_mapping, text_or_none
from .models import AgentBindingContext


def _copy_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def authority_boundary() -> dict[str, Any]:
    return {
        "authority_class": c.AUTHORITY_CLASS,
        "binding_or_intake_record_is_not_live_order_authority": True,
        "binding_or_intake_record_is_not_runtime_authority": True,
        "binding_or_intake_record_is_not_connector_semantic_binding": True,
        "binding_or_intake_record_is_not_replay_or_paper_result": True,
        "binding_or_intake_record_is_not_scoring_trade_selection": True,
        "binding_or_intake_record_is_not_optimizer_execution": True,
        "binding_or_intake_record_is_not_quantum_backend_execution": True,
        "binding_or_intake_record_is_not_profit_evidence": True,
        **dict(c.AUTHORITY_BOUNDARY_FALSE_FLAGS),
    }


def _pr155_registry_ref(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_path": c.PR155_REGISTRY_PATH.as_posix(),
        "registry_record_id": record.get("registry_record_id"),
        "source_pr154_record_id": record.get("source_pr154_record_id"),
        "agent_consumable_default_ready_flag": record.get(
            "agent_consumable_default_ready_flag"
        ),
        "registry_consumption_state": record.get("registry_consumption_state"),
        "owner_internal_policy_basis_or_null": record.get(
            "owner_internal_policy_basis_or_null"
        ),
    }


def _pr154_completion_ref(record: Mapping[str, Any]) -> dict[str, Any] | None:
    source_id = text_or_none(record.get("source_pr154_record_id"))
    if source_id is None:
        return None
    completion = as_mapping(record.get("blocked_completion_path_if_any"))
    return {
        "artifact_path": c.PR154_REPORT_PATH.as_posix(),
        "source_pr154_record_id": source_id,
        "completion_path_fields": {
            field: completion.get(field) for field in c.COMPLETION_PATH_FIELDS
        }
        if completion
        else None,
    }


def _source_record_ref(record: Mapping[str, Any]) -> str:
    return str(record.get("registry_record_id") or record.get("source_pr154_record_id"))


def build_pr155_ready_binding_record(
    record: Mapping[str, Any],
    *,
    binding_context: AgentBindingContext,
    pr155_authority_class: str,
) -> dict[str, Any]:
    source_ref = _source_record_ref(record)
    binding = binding_for_pr155_record(source_ref, binding_context)
    bound = binding["agent_binding_state"] in {
        c.AGENT_BOUND_NONLIVE_EXPLICIT,
        c.ROLE_BOUND_NONLIVE_EXPLICIT,
        c.CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT,
    }
    applicability = applicability_for_pr155_record(record)
    return {
        "pr156_record_id": f"PR156__PR155_BINDING__{source_ref}",
        "record_kind": c.PR155_DEFAULT_BINDING_RECORD,
        "source_population": c.SOURCE_POPULATION_PR155_READY,
        "source_record_ref": source_ref,
        "source_record_type": c.SOURCE_RECORD_TYPE_PR155_REGISTRY_RECORD,
        "source_artifact_path": c.PR155_REGISTRY_PATH.as_posix(),
        "source_authority_class": record.get("source_authority_class"),
        "population_lane": (
            c.PR155_READY_DEFAULT_BINDING_LANE
            if bound
            else c.PR155_READY_DEFAULT_BINDING_PENDING_LANE
        ),
        **binding,
        "template_type": None,
        "candidate_instance_state": c.CANDIDATE_INSTANCE_PENDING_CLASSIFICATION,
        "candidate_origin": c.SOURCE_POPULATION_PR155_READY,
        "candidate_origin_authority_class": pr155_authority_class,
        "candidate_research_intake_state": c.SOURCE_EVIDENCE_REFERENCED_ONLY,
        "applicability_class": applicability,
        "owner_strategy_priority_state": c.STRATEGY_PRIORITY_PENDING_OWNER_POLICY,
        "atomicrows_ingestion_state": c.ATOMICROWS_COMPATIBLE_EXISTING_PR155_DEFAULT,
        "scoring_ranking_readiness_state": (
            c.SCORING_RANKING_ELIGIBLE_NONLIVE
            if bound
            else c.SCORING_RANKING_PENDING_AGENT_BINDING
        ),
        "optimizer_routing_hint": population_optimizer_hint(applicability),
        "replay_paper_routing_hint": (
            c.REPLAY_PAPER_FUTURE_CANDIDATE
            if bound
            else c.REPLAY_PAPER_PENDING_AGENT_BINDING
        ),
        "market_scope": record.get("market_scope"),
        "platform_scope": record.get("platform_scope"),
        "route_triage_domain": record.get("route_triage_domain"),
        "launch_readiness_domain": record.get("launch_readiness_domain"),
        "section_crosswalk_refs": _copy_list(record.get("section_crosswalk_refs")),
        "market_specific_index_refs": _copy_list(record.get("market_specific_index_refs")),
        "command_action_matrix_refs": _copy_list(record.get("command_action_matrix_refs")),
        "atomicrows_reconciliation_refs": _copy_list(
            record.get("atomicrows_reconciliation_refs")
        ),
        "atomicrows_semantic_contract_refs": _copy_list(
            record.get("atomicrows_semantic_contract_refs")
        ),
        "pr155_registry_ref": _pr155_registry_ref(record),
        "pr154_completion_ref": _pr154_completion_ref(record),
        "blocked_completion_path_ref_or_inline": None,
        "future_completion_pr_hint": c.FUTURE_COMPLETION_PR_HINT,
        "future_scoring_ranking_pr_hint": c.FUTURE_SCORING_RANKING_PR_HINT,
        "future_optimizer_pr_hint": c.FUTURE_OPTIMIZER_PR_HINT,
        "future_replay_paper_pr_hint": c.FUTURE_REPLAY_PAPER_PR_HINT,
        **dict(c.NON_AUTHORITY_BOUNDARY),
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY),
        "created_by_pr": c.PR_ID,
        "authority_boundary": authority_boundary(),
    }


def build_pr154_blocked_ingestion_record(
    record: Mapping[str, Any],
    *,
    pr155_authority_class: str,
) -> dict[str, Any]:
    source_ref = text_or_none(record.get("source_pr154_record_id")) or _source_record_ref(record)
    completion = {
        field: as_mapping(record.get("blocked_completion_path_if_any")).get(field)
        for field in c.COMPLETION_PATH_FIELDS
    }
    applicability = applicability_for_pr155_record(record)
    return {
        "pr156_record_id": f"PR156__PR154_BLOCKED_INGESTION__{source_ref}",
        "record_kind": c.PR154_BLOCKED_INGESTION_RECORD,
        "source_population": c.SOURCE_POPULATION_PR154_BLOCKED,
        "source_record_ref": _source_record_ref(record),
        "source_record_type": c.SOURCE_RECORD_TYPE_PR154_BLOCKED_RECORD,
        "source_artifact_path": c.PR155_REGISTRY_PATH.as_posix(),
        "source_authority_class": record.get("source_authority_class"),
        "population_lane": c.PR154_BLOCKED_COMPLETION_INGESTION_LANE,
        "agent_binding_state": c.BINDING_PENDING_PR154_COMPLETION,
        "bound_agent_ids": [],
        "bound_agent_roles": [],
        "bound_consumer_classes": [],
        "binding_basis_artifacts": [
            c.PR155_REGISTRY_PATH.as_posix(),
            c.PR154_REPORT_PATH.as_posix(),
        ],
        "binding_basis_reason": c.BLOCKED_PR154_BINDING_REASON,
        "binding_block_codes": [c.PR156_PR154_COMPLETION_REQUIRED],
        "template_type": None,
        "candidate_instance_state": c.CANDIDATE_INSTANCE_BLOCKED,
        "candidate_origin": c.SOURCE_POPULATION_PR154_BLOCKED,
        "candidate_origin_authority_class": pr155_authority_class,
        "candidate_research_intake_state": c.SOURCE_EVIDENCE_BLOCKED_INSUFFICIENT_EVIDENCE,
        "applicability_class": applicability,
        "owner_strategy_priority_state": c.STRATEGY_PRIORITY_BLOCKED,
        "atomicrows_ingestion_state": c.ATOMICROWS_PENDING_PR154_COMPLETION,
        "scoring_ranking_readiness_state": c.SCORING_RANKING_BLOCKED,
        "optimizer_routing_hint": c.OPTIMIZER_ROUTING_BLOCKED,
        "replay_paper_routing_hint": c.REPLAY_PAPER_PENDING_ATOMICROWS_COMPLETION,
        "market_scope": record.get("market_scope"),
        "platform_scope": record.get("platform_scope"),
        "route_triage_domain": record.get("route_triage_domain"),
        "launch_readiness_domain": record.get("launch_readiness_domain"),
        "section_crosswalk_refs": _copy_list(record.get("section_crosswalk_refs")),
        "market_specific_index_refs": _copy_list(record.get("market_specific_index_refs")),
        "command_action_matrix_refs": _copy_list(record.get("command_action_matrix_refs")),
        "atomicrows_reconciliation_refs": _copy_list(
            record.get("atomicrows_reconciliation_refs")
        ),
        "atomicrows_semantic_contract_refs": _copy_list(
            record.get("atomicrows_semantic_contract_refs")
        ),
        "pr155_registry_ref": _pr155_registry_ref(record),
        "pr154_completion_ref": _pr154_completion_ref(record),
        "blocked_completion_path_ref_or_inline": completion,
        "future_completion_pr_hint": c.FUTURE_COMPLETION_PR_HINT,
        "future_scoring_ranking_pr_hint": c.FUTURE_SCORING_RANKING_PR_HINT,
        "future_optimizer_pr_hint": c.FUTURE_OPTIMIZER_PR_HINT,
        "future_replay_paper_pr_hint": c.FUTURE_REPLAY_PAPER_PR_HINT,
        **dict(c.NON_AUTHORITY_BOUNDARY),
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY),
        "created_by_pr": c.PR_ID,
        "authority_boundary": authority_boundary(),
    }
