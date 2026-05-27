"""Map PR154 materialization records into PR155 registry records."""

from __future__ import annotations

from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.atomicrows_parameter_default_value_materialization_gate import (
    taxonomy as pr154_tx,
)

from . import constants as c
from .io import as_list, text_or_none


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _non_empty(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return bool(_text(value).strip())


def _stable_record_id(record: Mapping[str, Any], index: int) -> str:
    source_pr154 = text_or_none(record.get("pr154_record_id"))
    source_target = text_or_none(record.get("source_pr153s_target_id"))
    if source_pr154:
        return f"{c.PR_ID}__{source_pr154}"
    if source_target:
        return f"{c.PR_ID}__{source_target}"
    return f"{c.PR_ID}__SCHEMA_INVALID_RECORD_INDEX_{index:04d}"


def _source_target_id(record: Mapping[str, Any]) -> str | None:
    return text_or_none(
        record.get("source_pr153s_target_id")
        or record.get("pr153s_canonical_identity_key")
    )


def _authority_boundary() -> dict[str, Any]:
    return {
        "authority_class": c.AUTHORITY_CLASS,
        "registry_default_is_not_direct_agent_assignment": True,
        "registry_default_is_not_connector_bound": True,
        "registry_default_is_not_runtime_ready": True,
        "registry_default_is_not_live_order_ready": True,
        "registry_default_is_not_replay_tested": True,
        "registry_default_is_not_paper_approved": True,
        "registry_default_is_not_quantum_execution_evidence": True,
        "registry_default_is_not_profit_evidence": True,
        **{field: False for field in c.RECORD_ALWAYS_FALSE_FIELDS},
    }


def _completion_path(record: Mapping[str, Any]) -> dict[str, Any]:
    return {field: record.get(field) for field in c.COMPLETION_PATH_FIELDS}


def _explicit_agent_ids(record: Mapping[str, Any]) -> list[str]:
    for key in (
        "eligible_agent_ids",
        "explicit_eligible_agent_ids",
        "agent_allowlist",
        "allowed_agent_ids",
    ):
        values = [str(item) for item in as_list(record.get(key)) if str(item).strip()]
        if values:
            return sorted(dict.fromkeys(values))
    return []


def _explicit_forbidden_agent_ids(record: Mapping[str, Any]) -> list[str]:
    for key in ("forbidden_agent_ids", "blocked_agent_ids", "agent_blocklist"):
        values = [str(item) for item in as_list(record.get(key)) if str(item).strip()]
        if values:
            return sorted(dict.fromkeys(values))
    return []


def _ready_default_use_class(record: Mapping[str, Any]) -> str:
    authority = record.get("materialized_value_authority_class")
    if authority in c.PR154_OFFICIAL_SOURCE_AUTHORITY_CLASSES:
        return c.NONLIVE_OFFICIAL_SOURCE_MATERIALIZED_DEFAULT
    if authority in c.PR154_OWNER_INTERNAL_AUTHORITY_CLASSES:
        return c.NONLIVE_OWNER_INTERNAL_POLICY_DEFAULT
    return c.NONLIVE_CONTROL_PLANE_METADATA_DEFAULT


def _owner_internal_basis(record: Mapping[str, Any]) -> Any:
    if record.get("materialized_value_authority_class") not in (
        c.PR154_OWNER_INTERNAL_AUTHORITY_CLASSES
    ):
        return None
    return {
        "authority_ref": record.get("materialized_value_authority_ref"),
        "policy_source_path": record.get("materialized_value_source_path"),
        "policy_source_key": record.get("materialized_value_source_record_key"),
        "policy_source_field": record.get("materialized_value_source_field_path"),
    }


def _route_triage_ref(payloads: Mapping[str, Mapping[str, Any]]) -> str:
    route = payloads.get("route_triage", {})
    return str(route.get("receipt_type") or c.NO_EXACT_PR136_RECORD_MAPPING)


def _section_crosswalk_refs(payloads: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    crosswalk = payloads.get("section_crosswalk_or_successor", {})
    return [
        {
            "mapping_state": c.NO_EXACT_PR136_RECORD_MAPPING,
            "receipt_type": crosswalk.get("receipt_type"),
            "domain_record_count": len(as_list(crosswalk.get("domain_records"))),
            "selected_path": (
                c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
                if crosswalk.get("receipt_type")
                == "PR136_MASTER_PLAN_SECTION_CROSSWALK"
                else c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH.as_posix()
            ),
        }
    ]


def _market_specific_index_refs(
    record: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    market = text_or_none(record.get("market_scope_if_available") or record.get("platform_scope"))
    scopes = as_list(payloads.get("market_specific_index", {}).get("market_scopes"))
    matches = [
        {
            "canonical_venue_id": scope.get("canonical_venue_id"),
            "market_scope_id": scope.get("market_scope_id"),
            "future_prs_required": as_list(scope.get("future_prs_required")),
            "missing_connector_semantic_bindings": scope.get(
                "missing_connector_semantic_bindings"
            ),
            "missing_runtime_cash_private_state_receipts": scope.get(
                "missing_runtime_cash_private_state_receipts"
            ),
            "missing_replay_paper_evidence": scope.get("missing_replay_paper_evidence"),
        }
        for scope in scopes
        if isinstance(scope, Mapping) and scope.get("canonical_venue_id") == market
    ]
    if matches:
        return matches
    return [
        {
            "mapping_state": c.NO_EXACT_PR136_RECORD_MAPPING,
            "record_market_scope": market,
            "report_path": c.PR136_MARKET_INDEX_PATH.as_posix(),
        }
    ]


def _command_action_matrix_refs(
    payloads: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    actions = as_list(payloads.get("command_action_matrix", {}).get("actions"))
    return [
        {
            "report_path": c.PR136_COMMAND_MATRIX_PATH.as_posix(),
            "action_ids": sorted(
                str(action.get("action_id"))
                for action in actions
                if isinstance(action, Mapping) and action.get("action_id")
            ),
            "all_actions_non_authority": all(
                not bool(action.get(field))
                for action in actions
                if isinstance(action, Mapping)
                for field in (
                    "creates_live_data",
                    "creates_source_retrieval",
                    "creates_source_acceptance",
                    "creates_connector_binding",
                    "creates_private_state_fetch",
                    "creates_runtime_cash_authority",
                    "creates_replay_execution",
                    "creates_paper_execution",
                    "creates_order_authority",
                    "creates_order_execution",
                    "creates_profit_evidence",
                    "creates_quantum_execution",
                    "creates_quantum_optimizer_input",
                    "creates_quantum_advantage_claim",
                    "creates_atomicrows_bundle",
                    "creates_atomicrows_rows",
                )
            ),
        }
    ]


def _atomicrows_reconciliation_refs(
    payloads: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reconciliation = payloads.get("atomicrows_reconciliation", {})
    validation = reconciliation.get("atomicrows_validation_state")
    validation_map = validation if isinstance(validation, Mapping) else {}
    return [
        {
            "report_path": c.PR137R_RECONCILIATION_PATH.as_posix(),
            "report_type": reconciliation.get("report_type"),
            "row_count_proven": validation_map.get("row_count_proven"),
            "row_count_value": validation_map.get("row_count_value"),
            "bundle_authority_created": reconciliation.get("not_created_flags", {}).get(
                "atomicrows_bundle_created"
            ),
        }
    ]


def _atomicrows_semantic_contract_refs(
    payloads: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    contract_report = payloads.get("atomicrows_semantic_contract", {})
    semantic_contract = contract_report.get("semantic_contract")
    semantic_map = semantic_contract if isinstance(semantic_contract, Mapping) else {}
    return [
        {
            "report_path": c.PR138_SEMANTIC_CONTRACT_PATH.as_posix(),
            "report_type": contract_report.get("report_type"),
            "required_field_count": contract_report.get("required_field_count"),
            "required_field_group_count": contract_report.get(
                "required_field_group_count"
            ),
            "field_inventory_path": semantic_map.get("field_inventory_path"),
            "semantic_row_values_materialized_by_pr138": contract_report.get(
                "semantic_row_values_materialized_by_pr138"
            ),
        }
    ]


def _atomicrows_state(
    record: Mapping[str, Any],
    preflight_allowed: bool,
    payloads: Mapping[str, Mapping[str, Any]],
) -> str:
    if not payloads.get("atomicrows_reconciliation"):
        return c.ATOMICROWS_BLOCKED_RECONCILIATION_MISSING
    if not payloads.get("atomicrows_semantic_contract"):
        return c.ATOMICROWS_BLOCKED_SEMANTIC_CONTRACT_MISSING
    if record.get("materialization_allowed") is not True:
        return c.ATOMICROWS_BLOCKED_PR154_INCOMPLETE
    if preflight_allowed:
        return c.ATOMICROWS_COMPATIBLE_PR154_MATERIALIZED_DEFAULT
    return c.ATOMICROWS_COMPATIBLE_PARTIAL_ORCHESTRATION


def _quantum_state(record: Mapping[str, Any]) -> str:
    quantum_class = record.get("quantum_forward_compatibility_class")
    if quantum_class == pr154_tx.QUANTUM_FORWARD_NOT_APPLICABLE:
        return c.QUANTUM_NOT_APPLICABLE_CLASSICAL_ONLY
    if quantum_class in {
        pr154_tx.QUANTUM_FORWARD_METADATA_ONLY,
        pr154_tx.QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY,
    }:
        return c.QUANTUM_FORWARD_METADATA_READY_NOT_EXECUTION
    if quantum_class == pr154_tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED:
        return c.QUANTUM_FORWARD_METADATA_PARTIAL_NOT_EXECUTION
    if quantum_class:
        return c.QUANTUM_FORWARD_METADATA_PARTIAL_NOT_EXECUTION
    return c.QUANTUM_FORWARD_METADATA_BLOCKED_MISSING_CLASSIFICATION


def _optimizer_hint(record: Mapping[str, Any]) -> str:
    route = record.get("quantum_optimizer_default_route")
    if route == pr154_tx.QUANTUM_OPTIMIZER_ROUTE_NOT_APPLICABLE:
        return c.OPTIMIZER_METADATA_MISSING
    if route == pr154_tx.QUANTUM_OPTIMIZER_ROUTE_METADATA_ONLY:
        return c.OPTIMIZER_METADATA_READY_NOT_EXECUTION
    if route == pr154_tx.QUANTUM_OPTIMIZER_ROUTE_EXECUTION_EVIDENCE_REQUIRED:
        return c.OPTIMIZER_METADATA_PARTIAL_NOT_EXECUTION
    return c.OPTIMIZER_METADATA_MISSING


def _latency_path_state(record: Mapping[str, Any]) -> str:
    if record.get("materialization_allowed") is True and record.get(
        "low_latency_hot_path_eligibility"
    ):
        return c.LATENCY_METADATA_READY_FOR_FUTURE_ROUTING
    if record.get("low_latency_hot_path_eligibility"):
        return c.CONTROL_PLANE_NONLIVE_METADATA_ONLY
    return c.LATENCY_METADATA_MISSING


def _ready_block_codes(record: Mapping[str, Any], preflight_allowed: bool) -> list[str]:
    block_codes: list[str] = []
    if not preflight_allowed:
        block_codes.append(c.PR155_ORCHESTRATION_ARTIFACT_MISSING)
    if record.get("materialized_value") is None:
        block_codes.append(c.PR155_READY_RECORD_VALUE_MISSING)
    if record.get("materialized_value_authority_class") not in (
        c.PR154_ALLOWED_AUTHORITY_CLASSES
    ):
        block_codes.append(c.PR155_READY_RECORD_AUTHORITY_INVALID)
    if record.get("materialized_value_authority_class") in (
        c.PR154_OFFICIAL_SOURCE_AUTHORITY_CLASSES
    ):
        for key in (
            "materialized_value_source_path",
            "materialized_value_source_record_key",
            "official_source_locator",
            "quote_span_or_machine_field_locator",
        ):
            if not _non_empty(record.get(key)):
                block_codes.append(c.PR155_READY_RECORD_PROVENANCE_MISSING)
                break
    if record.get("materialized_value_authority_class") in (
        c.PR154_OWNER_INTERNAL_AUTHORITY_CLASSES
    ) and not _non_empty(record.get("materialized_value_authority_ref")):
        block_codes.append(c.PR155_READY_RECORD_PROVENANCE_MISSING)
    return sorted(set(block_codes))


def map_pr154_record(
    record: Mapping[str, Any],
    *,
    index: int,
    preflight_allowed: bool,
    payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    registry_record_id = _stable_record_id(record, index)
    source_pr154_record_id = text_or_none(record.get("pr154_record_id"))
    source_target = _source_target_id(record)
    explicit_agents = _explicit_agent_ids(record)
    forbidden_agents = _explicit_forbidden_agent_ids(record)
    materialized = record.get("materialization_allowed") is True
    ready_block_codes = _ready_block_codes(record, preflight_allowed) if materialized else []
    registry_ready = materialized and not ready_block_codes

    if registry_ready and explicit_agents:
        registry_state = c.REGISTRY_READY_NONLIVE_EXPLICIT_AGENT_BINDING
        agent_assignment_state = c.EXPLICIT_AGENT_ALLOWLIST_BOUND
        direct_agent_ready = True
        eligible_basis = "EXPLICIT_AGENT_ALLOWLIST_FROM_CONSUMED_ARTIFACTS"
        agent_binding_block_codes: list[str] = []
        non_live_reason = c.NONLIVE_REGISTRY_REASON
    elif registry_ready:
        registry_state = c.REGISTRY_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING
        agent_assignment_state = c.AGENT_ASSIGNMENT_PENDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = [c.DIRECT_AGENT_BINDING_PENDING_BLOCK_CODE]
        non_live_reason = c.NONLIVE_PENDING_AGENT_BINDING_REASON
    elif materialized and c.PR155_READY_RECORD_VALUE_MISSING in ready_block_codes:
        registry_state = c.NON_CONSUMABLE_BLOCKED_VALUE_MISSING
        agent_assignment_state = c.AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = ready_block_codes
        non_live_reason = c.NONLIVE_BLOCKED_PR154_REASON
    elif materialized and c.PR155_READY_RECORD_AUTHORITY_INVALID in ready_block_codes:
        registry_state = c.NON_CONSUMABLE_BLOCKED_AUTHORITY_MISSING
        agent_assignment_state = c.AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = ready_block_codes
        non_live_reason = c.NONLIVE_BLOCKED_PR154_REASON
    elif materialized and c.PR155_READY_RECORD_PROVENANCE_MISSING in ready_block_codes:
        registry_state = c.NON_CONSUMABLE_BLOCKED_PROVENANCE_MISSING
        agent_assignment_state = c.AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = ready_block_codes
        non_live_reason = c.NONLIVE_BLOCKED_PR154_REASON
    elif materialized and not preflight_allowed:
        registry_state = c.NON_CONSUMABLE_BLOCKED_ORCHESTRATION_PRECHECK
        agent_assignment_state = c.AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = ready_block_codes
        non_live_reason = c.NONLIVE_BLOCKED_PR154_REASON
    else:
        registry_state = c.NON_CONSUMABLE_BLOCKED_PR154_INCOMPLETE
        agent_assignment_state = c.AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING
        direct_agent_ready = False
        eligible_basis = c.ELIGIBLE_AGENT_BASIS_PENDING
        agent_binding_block_codes = [
            str(record.get("materialization_block_code") or c.NON_CONSUMABLE_BLOCKED_PR154_INCOMPLETE)
        ]
        non_live_reason = c.NONLIVE_BLOCKED_PR154_REASON

    return {
        "registry_record_id": registry_record_id,
        "source_pr154_record_id": source_pr154_record_id,
        "source_target_id_or_atomic_row_id": source_target,
        "source_materialization_lane": (
            record.get("pr153s_materialization_route")
            or record.get("materialization_decision")
        ),
        "source_authority_class": record.get("materialized_value_authority_class"),
        "value": record.get("materialized_value"),
        "value_type": record.get("materialized_value_type"),
        "unit_or_basis": record.get("materialized_value_unit"),
        "scale": record.get("materialized_value_scale"),
        "source_value_status": record.get("materialization_decision"),
        "default_use_class": (
            _ready_default_use_class(record)
            if registry_ready
            else c.NONCONSUMABLE_BLOCKED_RECORD
        ),
        "registry_consumption_state": registry_state,
        "agent_assignment_state": agent_assignment_state,
        "agent_consumable_default_ready_flag": registry_ready,
        "direct_agent_assignment_ready_flag": direct_agent_ready,
        **{field: False for field in c.RECORD_ALWAYS_FALSE_FIELDS},
        "source_packet_path_or_null": record.get("materialized_value_source_path"),
        "source_candidate_packet_id_or_null": record.get(
            "materialized_value_source_record_key"
        ),
        "official_url_or_null": record.get("official_source_locator"),
        "quote_span_or_machine_field_locator_or_null": record.get(
            "quote_span_or_machine_field_locator"
        ),
        "owner_internal_policy_basis_or_null": _owner_internal_basis(record),
        "eligible_agent_ids": explicit_agents,
        "eligible_agent_basis": eligible_basis,
        "forbidden_agent_ids": forbidden_agents,
        "forbidden_agent_basis": (
            "EXPLICIT_FORBIDDEN_AGENT_LIST_FROM_CONSUMED_ARTIFACTS"
            if forbidden_agents
            else c.FORBIDDEN_AGENT_BASIS_UNDECLARED
        ),
        "agent_binding_block_codes": agent_binding_block_codes,
        "decision_family_scope": record.get("parameter_family_or_target_family"),
        "allowed_profile_bundle_ids": [],
        "market_scope": record.get("market_scope_if_available"),
        "platform_scope": record.get("platform_scope"),
        "launch_readiness_domain": c.NO_EXACT_PR136_RECORD_MAPPING,
        "route_triage_domain": _route_triage_ref(payloads),
        "section_crosswalk_refs": _section_crosswalk_refs(payloads),
        "market_specific_index_refs": _market_specific_index_refs(record, payloads),
        "command_action_matrix_refs": _command_action_matrix_refs(payloads),
        "atomicrows_reconciliation_refs": _atomicrows_reconciliation_refs(payloads),
        "atomicrows_semantic_contract_refs": _atomicrows_semantic_contract_refs(payloads),
        "atomicrows_compatibility_state": _atomicrows_state(
            record,
            preflight_allowed,
            payloads,
        ),
        "quantum_forward_compatibility_state": _quantum_state(record),
        "quantum_applicability_hint": record.get("quantum_forward_compatibility_class"),
        "quantum_strategy_compatibility_tags": [],
        "optimizer_readiness_hint": _optimizer_hint(record),
        "latency_path_state": _latency_path_state(record),
        "latency_sensitivity_hint": (
            record.get("low_latency_hot_path_eligibility")
            or c.LATENCY_METADATA_NOT_EXPLICIT
        ),
        "risk_sensitivity_hint": c.RISK_METADATA_NOT_EXPLICIT,
        "consumer_gate_block_codes": [] if registry_ready else agent_binding_block_codes,
        "non_live_reason": non_live_reason,
        "blocked_completion_path_if_any": (
            None if registry_ready else _completion_path(record)
        ),
        "future_replay_paper_placement_hint": c.FUTURE_REPLAY_PAPER_PLACEMENT_HINT,
        "future_live_transition_block_reason": c.FUTURE_LIVE_TRANSITION_BLOCK_REASON,
        "created_by_pr": c.PR_ID,
        "authority_boundary": _authority_boundary(),
    }
