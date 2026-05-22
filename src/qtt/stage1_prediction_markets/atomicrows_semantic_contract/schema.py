"""PR138 semantic row-contract schema and inventory builders."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from . import constants as c


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _field_group_id(field_id: str) -> str:
    for group_id, fields in c.REQUIRED_FIELDS_BY_GROUP:
        if field_id in fields:
            return group_id
    raise KeyError(field_id)


def _field_group_record(group: Mapping[str, Any]) -> dict[str, Any]:
    fields = list(group["fields"])
    return {
        "field_count": len(fields),
        "field_group_id": str(group["field_group_id"]),
        "field_group_ordinal": int(group["field_group_ordinal"]),
        "fields": fields,
        "title": str(group["title"]),
    }


def field_group_records() -> list[dict[str, Any]]:
    return [_field_group_record(group) for group in c.FIELD_GROUPS]


def _trace_or_blocker(
    trace: Mapping[str, Any],
    *,
    missing_reason: str,
    blocker_state: str,
) -> dict[str, Any]:
    if trace.get("trace_state") == "TRACE_CONSUMED_READ_ONLY":
        return dict(trace)
    return {
        "blocker_state": blocker_state,
        "reason_code": missing_reason,
        "trace_state": "TRACE_BLOCKED",
    }


def _field_reason_codes(field_id: str) -> list[str]:
    reason_codes = list(c.FIELD_DEFAULT_REASON_CODES)
    if field_id == "live_use_allowed_flag":
        reason_codes.append(c.PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN)
    if field_id == "order_authority_created_flag":
        reason_codes.append(c.PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN)
    if field_id == "profit_evidence_created_flag":
        reason_codes.append(c.PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN)
    if field_id == "quantum_backend_execution_allowed_flag":
        reason_codes.append(c.PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN)
    if field_id == "external_fact_authority_flag":
        reason_codes.append(
            c.PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET
        )
    return reason_codes


def _accepted_source_required(field_id: str, group_id: str) -> bool:
    return (
        group_id in {"MARKET_VENUE_SCOPE", "TRADING_OBJECTIVE_SUPPORT", "SOURCE_PROVENANCE_BOUNDARY"}
        or field_id in {"execution_family", "liquidity_context_family"}
    )


def field_inventory_records(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    route_trace = _trace_or_blocker(
        evidence.get("route_triage_trace", {}),
        missing_reason=c.PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING,
        blocker_state="BLOCKED_PENDING_ROUTE_CROSSWALK_TRACE",
    )
    market_trace = _trace_or_blocker(
        evidence.get("market_specific_section_index_trace", {}),
        missing_reason=c.PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING,
        blocker_state="BLOCKED_PENDING_MARKET_INDEX_TRACE",
    )
    command_trace = _trace_or_blocker(
        evidence.get("command_action_matrix_trace", {}),
        missing_reason=c.PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING,
        blocker_state="BLOCKED_PENDING_COMMAND_ACTION_MATRIX_TRACE",
    )
    crosswalk_by_section = evidence.get("section_crosswalk_by_section_id", {})
    if not isinstance(crosswalk_by_section, Mapping):
        crosswalk_by_section = {}

    ordinal = 0
    for group_id, fields in c.REQUIRED_FIELDS_BY_GROUP:
        section_id = c.FIELD_GROUP_SECTION_TRACE[group_id]
        section_trace = crosswalk_by_section.get(section_id)
        if isinstance(section_trace, Mapping):
            crosswalk_trace = {
                "artifact_paths": list(evidence.get("section_crosswalk_artifacts", [])),
                "crosswalk_entry_consumed_read_only": True,
                "no_claim_boundary_summary": (
                    "STATIC_METADATA_TRACE_ONLY_NO_ATOMICROWS_MUTATION_NO_FINAL_READINESS"
                ),
                "section_id": section_trace.get("section_id"),
                "trace_state": "TRACE_CONSUMED_READ_ONLY",
            }
        else:
            crosswalk_trace = {
                "blocker_state": "BLOCKED_PENDING_ROUTE_CROSSWALK_TRACE",
                "reason_code": c.PR138_REASON_SECTION_CROSSWALK_EVIDENCE_MISSING,
                "section_id": section_id,
                "trace_state": "TRACE_BLOCKED",
            }
        for field_id in fields:
            ordinal += 1
            accepted_source_required = _accepted_source_required(field_id, group_id)
            records.append(
                {
                    "accepted_source_packet_required_before_materialization": (
                        accepted_source_required
                    ),
                    "allowed_market_scopes": list(c.CANONICAL_STAGE1_MARKET_SCOPES),
                    "allowed_placeholder_states": list(c.ALLOWED_PLACEHOLDER_STATES),
                    "atomicrows_bundle_mutation_required_in_pr138": False,
                    "authority_boundary": c.AUTHORITY_BOUNDARY,
                    "canonical_name": field_id,
                    "canonical_venue_scope_values": list(c.CANONICAL_STAGE1_MARKET_SCOPES),
                    "command_action_matrix_trace": deepcopy(command_trace),
                    "connector_semantic_binding_created_by_field": False,
                    "field_group_id": group_id,
                    "field_id": field_id,
                    "field_ordinal": ordinal,
                    "full_master_plan_section_crosswalk_trace": deepcopy(crosswalk_trace),
                    "future_enrichment_phase": c.FIELD_GROUP_FUTURE_PHASE[group_id],
                    "future_pr_consumers": list(c.NEXT_REQUIRED_PRS),
                    "hot_path_dependency_created_by_field": False,
                    "live_authority_created_by_field": False,
                    "order_authority_created_by_field": False,
                    "owner_review_required_before_live_use": True,
                    "populated_by_pr138": False,
                    "precomputed_snapshot_compatibility_class": (
                        c.PRECOMPUTED_SNAPSHOT_COMPATIBILITY_CLASS
                    ),
                    "profit_evidence_created_by_field": False,
                    "pr138_inclusion_basis": (
                        "PR137R recorded this semantic contract surface as incomplete; "
                        "PR138 defines the contract only and leaves row values for future PRs."
                    ),
                    "quantum_execution_created_by_field": False,
                    "required_for_future_pr142_final_readiness": True,
                    "replay_paper_required_before_live_use": True,
                    "route_triage_trace": deepcopy(route_trace),
                    "row_family_source_mutation_required_in_pr138": False,
                    "runtime_cash_authority_created_by_field": False,
                    "scoring_ranking_arbitration_created_by_field": False,
                    "source_acceptance_created_by_field": False,
                    "trading_signal_created_by_field": False,
                    "value_kind": c.VALUE_KIND_BY_FIELD[field_id],
                    "validator_reason_codes": _field_reason_codes(field_id),
                    "market_specific_section_index_trace": deepcopy(market_trace),
                }
            )
    return records


def build_contract(evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "allowed_placeholder_states": list(c.ALLOWED_PLACEHOLDER_STATES),
        "authority_class": c.AUTHORITY_CLASS,
        "baseline_checkpoint": c.BASELINE_CHECKPOINT,
        "canonical_stage1_market_scopes": list(c.CANONICAL_STAGE1_MARKET_SCOPES),
        "contract_id": c.CONTRACT_ID,
        "contract_version": "v1",
        "field_groups": field_group_records(),
        "fields": field_inventory_records(evidence),
        "future_pr_phase_values": list(c.FUTURE_PR_PHASE_VALUES),
        "inventory_id": c.INVENTORY_ID,
        "pr_id": c.PR_ID,
        "required_field_count": c.REQUIRED_FIELD_COUNT,
        "required_field_group_count": c.REQUIRED_FIELD_GROUP_COUNT,
        "semantic_row_values_materialized_by_pr138": False,
    }


def _false_const_property() -> dict[str, Any]:
    return {"const": False}


def build_json_schema() -> dict[str, Any]:
    false_fields = {
        "atomicrows_bundle_mutation_required_in_pr138": _false_const_property(),
        "connector_semantic_binding_created_by_field": _false_const_property(),
        "hot_path_dependency_created_by_field": _false_const_property(),
        "live_authority_created_by_field": _false_const_property(),
        "order_authority_created_by_field": _false_const_property(),
        "populated_by_pr138": _false_const_property(),
        "profit_evidence_created_by_field": _false_const_property(),
        "quantum_execution_created_by_field": _false_const_property(),
        "row_family_source_mutation_required_in_pr138": _false_const_property(),
        "runtime_cash_authority_created_by_field": _false_const_property(),
        "scoring_ranking_arbitration_created_by_field": _false_const_property(),
        "source_acceptance_created_by_field": _false_const_property(),
        "trading_signal_created_by_field": _false_const_property(),
    }
    field_required = [
        "field_id",
        "field_group_id",
        "field_ordinal",
        "canonical_name",
        "value_kind",
        "required_for_future_pr142_final_readiness",
        "populated_by_pr138",
        "future_enrichment_phase",
        "authority_boundary",
        "live_authority_created_by_field",
        "order_authority_created_by_field",
        "profit_evidence_created_by_field",
        "quantum_execution_created_by_field",
        "source_acceptance_created_by_field",
        "connector_semantic_binding_created_by_field",
        "runtime_cash_authority_created_by_field",
        "scoring_ranking_arbitration_created_by_field",
        "trading_signal_created_by_field",
        "accepted_source_packet_required_before_materialization",
        "replay_paper_required_before_live_use",
        "owner_review_required_before_live_use",
        "atomicrows_bundle_mutation_required_in_pr138",
        "row_family_source_mutation_required_in_pr138",
        "hot_path_dependency_created_by_field",
        "precomputed_snapshot_compatibility_class",
        "route_triage_trace",
        "full_master_plan_section_crosswalk_trace",
        "market_specific_section_index_trace",
        "command_action_matrix_trace",
        "allowed_market_scopes",
        "canonical_venue_scope_values",
        "allowed_placeholder_states",
        "validator_reason_codes",
    ]
    return {
        "$id": c.CONTRACT_SCHEMA_ID,
        "$schema": "json-schema-draft-2020-12",
        "additionalProperties": False,
        "description": (
            "Static deterministic PR138 AtomicRows semantic row-contract schema. "
            "It defines field inventory metadata only and creates no AtomicRows row "
            "values, runtime, live, order, profit, source acceptance, connector "
            "binding, optimizer, or quantum execution authority."
        ),
        "properties": {
            "allowed_placeholder_states": {
                "const": list(c.ALLOWED_PLACEHOLDER_STATES)
            },
            "authority_class": {"const": c.AUTHORITY_CLASS},
            "baseline_checkpoint": {"const": c.BASELINE_CHECKPOINT},
            "canonical_stage1_market_scopes": {
                "const": list(c.CANONICAL_STAGE1_MARKET_SCOPES)
            },
            "contract_id": {"const": c.CONTRACT_ID},
            "contract_version": {"const": "v1"},
            "field_groups": {
                "items": {"$ref": "#/$defs/field_group"},
                "maxItems": c.REQUIRED_FIELD_GROUP_COUNT,
                "minItems": c.REQUIRED_FIELD_GROUP_COUNT,
                "type": "array",
            },
            "fields": {
                "items": {"$ref": "#/$defs/field_inventory_record"},
                "maxItems": c.REQUIRED_FIELD_COUNT,
                "minItems": c.REQUIRED_FIELD_COUNT,
                "type": "array",
            },
            "future_pr_phase_values": {"const": list(c.FUTURE_PR_PHASE_VALUES)},
            "inventory_id": {"const": c.INVENTORY_ID},
            "pr_id": {"const": c.PR_ID},
            "required_field_count": {"const": c.REQUIRED_FIELD_COUNT},
            "required_field_group_count": {"const": c.REQUIRED_FIELD_GROUP_COUNT},
            "semantic_row_values_materialized_by_pr138": {"const": False},
        },
        "required": [
            "contract_id",
            "contract_version",
            "pr_id",
            "authority_class",
            "baseline_checkpoint",
            "required_field_group_count",
            "required_field_count",
            "canonical_stage1_market_scopes",
            "allowed_placeholder_states",
            "future_pr_phase_values",
            "field_groups",
            "fields",
            "semantic_row_values_materialized_by_pr138",
            "inventory_id",
        ],
        "title": "PR138 AtomicRows Semantic Row Contract",
        "type": "object",
        "$defs": {
            "field_group": {
                "additionalProperties": False,
                "properties": {
                    "field_count": {"type": "integer"},
                    "field_group_id": {"enum": list(c.REQUIRED_FIELD_GROUP_IDS)},
                    "field_group_ordinal": {"type": "integer"},
                    "fields": {
                        "items": {"enum": list(c.REQUIRED_FIELD_IDS)},
                        "type": "array",
                    },
                    "title": {"type": "string"},
                },
                "required": [
                    "field_group_id",
                    "field_group_ordinal",
                    "title",
                    "field_count",
                    "fields",
                ],
                "type": "object",
            },
            "trace": {
                "additionalProperties": True,
                "properties": {
                    "trace_state": {
                        "enum": ["TRACE_CONSUMED_READ_ONLY", "TRACE_BLOCKED"]
                    }
                },
                "required": ["trace_state"],
                "type": "object",
            },
            "field_inventory_record": {
                "additionalProperties": False,
                "properties": {
                    **false_fields,
                    "accepted_source_packet_required_before_materialization": {
                        "type": "boolean"
                    },
                    "allowed_market_scopes": {
                        "const": list(c.CANONICAL_STAGE1_MARKET_SCOPES)
                    },
                    "allowed_placeholder_states": {
                        "const": list(c.ALLOWED_PLACEHOLDER_STATES)
                    },
                    "authority_boundary": {"const": c.AUTHORITY_BOUNDARY},
                    "canonical_name": {"enum": list(c.REQUIRED_FIELD_IDS)},
                    "canonical_venue_scope_values": {
                        "const": list(c.CANONICAL_STAGE1_MARKET_SCOPES)
                    },
                    "command_action_matrix_trace": {"$ref": "#/$defs/trace"},
                    "field_group_id": {"enum": list(c.REQUIRED_FIELD_GROUP_IDS)},
                    "field_id": {"enum": list(c.REQUIRED_FIELD_IDS)},
                    "field_ordinal": {"type": "integer"},
                    "full_master_plan_section_crosswalk_trace": {
                        "$ref": "#/$defs/trace"
                    },
                    "future_enrichment_phase": {
                        "enum": list(c.FUTURE_PR_PHASE_VALUES)
                    },
                    "future_pr_consumers": {"const": list(c.NEXT_REQUIRED_PRS)},
                    "owner_review_required_before_live_use": {"const": True},
                    "precomputed_snapshot_compatibility_class": {
                        "const": c.PRECOMPUTED_SNAPSHOT_COMPATIBILITY_CLASS
                    },
                    "pr138_inclusion_basis": {"type": "string"},
                    "required_for_future_pr142_final_readiness": {"const": True},
                    "replay_paper_required_before_live_use": {"const": True},
                    "route_triage_trace": {"$ref": "#/$defs/trace"},
                    "market_specific_section_index_trace": {"$ref": "#/$defs/trace"},
                    "validator_reason_codes": {
                        "items": {"type": "string"},
                        "minItems": 1,
                        "type": "array",
                    },
                    "value_kind": {"type": "string"},
                },
                "required": field_required,
                "type": "object",
            },
        },
    }


def write_schema_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    schema = build_json_schema()
    path = root / c.SCHEMA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(schema), encoding="utf-8", newline="\n")
    return schema


def write_inventory_file(repo_root: Path | str, contract: Mapping[str, Any]) -> None:
    root = Path(repo_root).resolve()
    path = root / c.INVENTORY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(dict(contract)), encoding="utf-8", newline="\n")
