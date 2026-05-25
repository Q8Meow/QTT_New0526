"""Validation and artifact writers for PR143 owner override currentization."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    BranchContext,
    current_branch_context,
    is_downstream_roadmap_branch,
    is_pr_or_later_branch,
)
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as pr152_constants,
)

from . import constants as c
from .builder import build_fixture, build_gate, build_report, json_dump, yaml_dump


def _array_schema(items: Sequence[str] | None = None) -> dict[str, Any]:
    item_schema: dict[str, Any] = {"type": "string"}
    if items is not None:
        item_schema["enum"] = list(items)
    return {"type": "array", "items": item_schema}


def _object_schema(
    properties: Mapping[str, Any],
    *,
    required: Sequence[str] | None = None,
    additional: bool = False,
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": additional,
        "properties": dict(properties),
        "required": list(required if required is not None else properties.keys()),
    }


def _false_boundary_schema(fields: Sequence[str]) -> dict[str, Any]:
    return _object_schema(
        {field: {"type": "boolean", "const": False} for field in fields},
        additional=False,
    )


def _true_boundary_schema(fields: Sequence[str]) -> dict[str, Any]:
    return _object_schema(
        {field: {"type": "boolean", "const": True} for field in fields},
        additional=False,
    )


def build_json_schema(repo_root: Path | str | None = None) -> dict[str, Any]:
    del repo_root
    no_claim = _false_boundary_schema(c.NO_CLAIM_FALSE_FIELDS)
    forbidden_payload = _false_boundary_schema(c.FORBIDDEN_PAYLOAD_FIELDS)
    non_owner_fabrication = _true_boundary_schema(c.FORBIDDEN_AUTHORITY_OUTPUT_FIELDS)
    false_creation = _false_boundary_schema(c.FORBIDDEN_CREATION_FALSE_FIELDS)
    quantum_planning_true = _true_boundary_schema(c.QUANTUM_PLANNING_ALLOWED_FIELDS)

    owner_directive = _object_schema(
        {
            "owner_global_override_declared": {"type": "boolean", "const": True},
            "owner_statement_recorded_normalized": {
                "type": "string",
                "const": c.OWNER_GLOBAL_OVERRIDE_CANONICAL_NORMALIZED_TEXT,
            },
            "owner_says_do_not_ask_again": {"type": "boolean", "const": True},
            "owner_directive_status": {
                "type": "string",
                "const": "ACTIVE_FOR_GLOBAL_INTERNAL_QTT_WORKFLOW_UNBLOCKING",
            },
            "owner_directive_scope": {
                "type": "string",
                "const": "GLOBAL_INTERNAL_QTT_WORKFLOW_GATES_AND_PERMISSIONS",
            },
            "owner_override_satisfies_internal_owner_approval": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_owner_approval_receipt": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_owner_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_materialization_planning_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_owner_action_required": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_owner_authorization_required_before_implementation": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_quantum_planning_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_quantum_optimization_architecture_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_true_quantum_backend_integration_planning_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_optimizer_planning_permission": {
                "type": "boolean",
                "const": True,
            },
            "owner_override_satisfies_internal_agent_orchestration_planning_permission": {
                "type": "boolean",
                "const": True,
            },
            "future_prompts_must_not_ask_owner_again_for_internal_qtt_approval": {
                "type": "boolean",
                "const": True,
            },
            "future_validators_must_not_reblock_on_owner_approval_for_internal_qtt_workflow": {
                "type": "boolean",
                "const": True,
            },
            "future_qtt_agents_must_treat_owner_internal_override_as_satisfied": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    release_contract = _object_schema(
        {
            "released_internal_gate_classes": {
                "type": "array",
                "items": {"type": "string", "enum": list(c.RELEASED_INTERNAL_GATE_CLASSES)},
            },
            "released_pr142_blocked_reason_codes": {
                "type": "array",
                "items": {"type": "string", "enum": list(c.OWNER_GATE_CODES_RELEASED_BY_PR143)},
            },
            "active_owner_approval_blockers_after_pr143": {
                "type": "array",
                "maxItems": 0,
            },
            "internal_owner_permission_state_after_pr143": {
                "type": "string",
                "const": c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143,
            },
            "future_reports_must_use_owner_global_override_satisfied_state": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    non_owner_boundary = _object_schema(
        {
            "preserved_non_owner_evidence_classes": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED),
                },
            },
            "non_owner_evidence_state_label": {
                "type": "string",
                "const": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            },
            **non_owner_fabrication["properties"],
        },
        additional=False,
    )

    pr142_handoff = _object_schema(
        {
            "upstream_report_path": {"type": "string", "const": c.PR142_REPORT_PATH.as_posix()},
            "upstream_yaml_path": {"type": "string", "const": c.PR142_YAML_PATH.as_posix()},
            "ready_to_request_owner_review": {"type": "boolean", "const": True},
            "ready_to_prepare_future_materialization_plan": {
                "type": "boolean",
                "const": True,
            },
            "required_future_owner_action": {
                "type": "string",
                "const": "EXPLICIT_OWNER_APPROVAL_PACKET_REQUIRED_BEFORE_MATERIALIZATION",
            },
            "readiness_state_before_pr143": {"type": "string"},
            "blocked_reason_codes_before_pr143": _array_schema(),
            "owner_gate_codes_released_by_pr143": {
                "type": "array",
                "items": {"type": "string", "enum": list(c.OWNER_GATE_CODES_RELEASED_BY_PR143)},
            },
            "non_owner_evidence_codes_preserved_by_pr143": _array_schema(),
            "readiness_state_after_pr143": {
                "type": "string",
                "const": c.READINESS_STATE_AFTER_PR143,
            },
            "materialization_permission_for_planning_released": {
                "type": "boolean",
                "const": True,
            },
            "materialization_permission_for_actual_value_writes_created": {
                "type": "boolean",
                "const": False,
            },
            "semantic_values_materialized": {"type": "boolean", "const": False},
            "bundle_mutation_created": {"type": "boolean", "const": False},
            "row_family_source_mutation_created": {"type": "boolean", "const": False},
        },
        additional=False,
    )

    source_boundary = _object_schema(
        {
            "source_evidence_packet_consumed_if_present": {"type": "boolean", "const": True},
            "owner_policy_may_authorize_retrieval_scope": {"type": "boolean", "const": True},
            "owner_policy_may_authorize_external_fact_value": {
                "type": "boolean",
                "const": False,
            },
            "source_acceptance_created": {"type": "boolean", "const": False},
            "connector_semantic_binding_created": {"type": "boolean", "const": False},
            "runtime_cash_receipt_created": {"type": "boolean", "const": False},
            "missing_accepted_source_packets_are_evidence_pending_not_owner_approval": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    quantum = _object_schema(
        {
            "owner_internal_permission_for_quantum_planning_satisfied": {
                "type": "boolean",
                "const": True,
            },
            "owner_internal_permission_for_quantum_optimization_architecture_satisfied": {
                "type": "boolean",
                "const": True,
            },
            "owner_internal_permission_for_true_quantum_backend_integration_planning_satisfied": {
                "type": "boolean",
                "const": True,
            },
            "quantum_planning_state": {
                "type": "string",
                "const": c.QUANTUM_PLANNING_STATE,
            },
            "quantum_forward_metadata_only": {"type": "boolean", "const": True},
            **quantum_planning_true["properties"],
            "true_quantum_backend_execution_created": {"type": "boolean", "const": False},
            "quantum_simulator_execution_created": {"type": "boolean", "const": False},
            "qaoa_execution_created": {"type": "boolean", "const": False},
            "vqe_execution_created": {"type": "boolean", "const": False},
            "annealing_execution_created": {"type": "boolean", "const": False},
            "qubo_solving_created": {"type": "boolean", "const": False},
            "ising_solving_created": {"type": "boolean", "const": False},
            "quantum_optimizer_input_output_created": {"type": "boolean", "const": False},
            "quantum_advantage_claim_created": {"type": "boolean", "const": False},
            "optimizer_parameter_value_source_status": {
                "type": "string",
                "const": "NOT_MATERIALIZED_OR_NOT_ACCEPTED",
            },
            "quantum_backend_result_status": {
                "type": "string",
                "const": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            },
            "quantum_simulator_result_status": {
                "type": "string",
                "const": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            },
            "parameter_ranges_invented": {"type": "boolean", "const": False},
            "optimizer_defaults_invented": {"type": "boolean", "const": False},
            "future_optimizer_compatibility_notes": _array_schema(),
        },
        additional=False,
    )

    classical = _object_schema(
        {
            "owner_internal_permission_for_optimizer_planning_satisfied": {
                "type": "boolean",
                "const": True,
            },
            "classical_optimizer_execution_created": {"type": "boolean", "const": False},
            "scoring_execution_created": {"type": "boolean", "const": False},
            "ranking_execution_created": {"type": "boolean", "const": False},
            "arbitration_execution_created": {"type": "boolean", "const": False},
            "strategy_selection_created": {"type": "boolean", "const": False},
            "deterministic_field_identity_ready": {"type": "boolean", "const": True},
            "external_fact_evidence_pending_not_owner_approval": {
                "type": "boolean",
                "const": True,
            },
            "replay_paper_results_pending_not_owner_approval": {
                "type": "boolean",
                "const": True,
            },
            "runtime_cash_receipt_pending_not_owner_approval": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    latency = _object_schema(
        {
            "control_plane_only": {"type": "boolean", "const": True},
            "live_pretrade_dependency_created": {"type": "boolean", "const": False},
            "live_path_import_created": {"type": "boolean", "const": False},
            "runtime_service_created": {"type": "boolean", "const": False},
            "order_router_dependency_created": {"type": "boolean", "const": False},
            "no_live_path_runtime_call": {"type": "boolean", "const": True},
            "no_doc_retrieval_in_live_path": {"type": "boolean", "const": True},
            "no_quantum_backend_call_in_live_path": {"type": "boolean", "const": True},
            "no_quantum_simulator_call_in_live_path": {"type": "boolean", "const": True},
            "no_optimizer_call_in_live_path": {"type": "boolean", "const": True},
            "owner_global_override_validation_not_live_hot_path_dependency": {
                "type": "boolean",
                "const": True,
            },
            "future_live_path_must_consume_precomputed_owner_override_snapshot_only": {
                "type": "boolean",
                "const": True,
            },
            "future_live_path_must_consume_precomputed_quantum_decision_snapshot_only": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://qtt.local/schemas/governance/"
            "qtt_owner_global_override_directive_currentization_and_internal_gate_release.schema.json"
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "report_type": {"type": "string", "const": c.REPORT_TYPE},
            "report_version": {"type": "string", "const": c.REPORT_VERSION},
            "artifact_stem": {"type": "string", "const": c.ARTIFACT_STEM},
            "authority_class": {"type": "string", "enum": list(c.AUTHORITY_CLASS_VALUES)},
            "generated_at_utc": {"type": "string", "const": c.STATIC_TIME},
            "generated_by_validator_tool": {"type": "boolean", "const": True},
            "generated_from_static_evidence_only": {"type": "boolean", "const": True},
            "pr_identity_resolution": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "repo_current_pr": {"type": "string", "const": c.PR_ID},
                    "github_pr_number": {
                        "type": "string",
                        "const": "OWNER_TO_ASSIGN_OR_UNKNOWN",
                    },
                    "roadmap_identity_inference_used": {
                        "type": "boolean",
                        "const": False,
                    },
                    "implementation_truth": {"type": "string"},
                    "owner_scope_basis": {
                        "type": "string",
                        "const": "OWNER_GLOBAL_OVERRIDE_DECLARED_BY_OWNER_IN_CURRENT_PROMPT",
                    },
                    "global_internal_qtt_override": {"type": "boolean", "const": True},
                    "immediate_atomicrows_consumer": {"type": "boolean", "const": True},
                    "does_not_replace_pr143k": {"type": "boolean", "const": True},
                    "pr143k_pr143p_pr143f_remain_downstream_evidence_lanes": {
                        "type": "boolean",
                        "const": True,
                    },
                },
            },
            "repo_status_preflight": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "local_main_verified": {"type": "boolean", "const": True},
                    "local_main_clean": {"type": "boolean", "const": True},
                    "main_head_short_sha_as_vcs_metadata_only": {"type": "string"},
                    "github_main_validation_status": {
                        "type": "string",
                        "enum": ["SUCCESS", "FAILED", "UNVERIFIED_NOT_CLAIMED"],
                    },
                    "github_status_claimed": {"type": "boolean"},
                    "branch_created_after_scope_receipt": {
                        "type": "boolean",
                        "const": True,
                    },
                },
            },
            "path_derivation_basis": {"type": "object"},
            "owner_global_override_directive": owner_directive,
            "internal_gate_release_contract": release_contract,
            "non_owner_evidence_boundary": non_owner_boundary,
            "pr142_handoff_consumption": pr142_handoff,
            "pr136_orchestration_preflight": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "consumed_files": _array_schema(),
                    "alias_resolution": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "requested_alias": {"type": "string"},
                            "alias_exists": {"type": "boolean"},
                            "canonical_crosswalk_used": {
                                "type": "string",
                                "const": c.CROSSWALK_CANONICAL.as_posix(),
                            },
                            "created_missing_alias": {"type": "boolean", "const": False},
                            "conflict_detected": {"type": "boolean", "const": False},
                        },
                    },
                    "route_triage_alignment": {"type": "object"},
                    "sequence_alignment": {"type": "object"},
                    "dependency_alignment": {"type": "object"},
                    "launch_readiness_domain_alignment": {"type": "object"},
                    "market_specific_alignment": {"type": "object"},
                    "command_action_alignment": {"type": "array"},
                    "quantum_atomicrows_optimization_readiness_alignment": {
                        "type": "object"
                    },
                    "agent_launch_orchestration_alignment": {"type": "object"},
                    "replay_paper_live_transition_boundary": {"type": "object"},
                    "pr136_planning_authority_only": {"type": "boolean", "const": True},
                    "pr136_does_not_authorize_materialization": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr136_does_not_authorize_live_trading": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr136_does_not_authorize_quantum_execution": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr136_does_not_authorize_day1_launch": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr143k_relationship": {"type": "string"},
                },
            },
            "pr143k_forward_handoff": _true_boundary_schema(
                c.DOWNSTREAM_PR143_COMPATIBILITY_FIELDS
            ),
            "source_evidence_boundary": source_boundary,
            "atomicrows_compatibility": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "enrichment_order_preserved": {"type": "boolean", "const": True},
                    "enrichment_order": _array_schema(),
                    "semantic_row_contract_preserved": {"type": "boolean", "const": True},
                    "row_family_source_manifest_preserved": {
                        "type": "boolean",
                        "const": True,
                    },
                    "field_coverage_plan_preserved": {"type": "boolean", "const": True},
                    "value_materialization_still_not_performed_by_this_pr": {
                        "type": "boolean",
                        "const": True,
                    },
                    "no_bundle_mutation": {"type": "boolean", "const": True},
                    "no_row_family_source_mutation": {"type": "boolean", "const": True},
                    "no_bundle_authority_created": {"type": "boolean", "const": True},
                    "no_bundle_freeze_authority_created": {
                        "type": "boolean",
                        "const": True,
                    },
                },
            },
            "quantum_forward_compatibility": quantum,
            "classical_optimizer_forward_compatibility": classical,
            "latency_hot_path_boundary": latency,
            "no_claim_boundary": no_claim,
            "forbidden_payload_boundary": forbidden_payload,
            "existing_owner_global_override_authority_consumption": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tool_path": {"type": "string"},
                    "report_path": {"type": "string"},
                    "tool_consumed": {"type": "boolean", "const": True},
                    "report_present": {"type": "boolean", "const": True},
                    "report_type": {
                        "type": "string",
                        "const": "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT",
                    },
                    "owner_global_override_authority": {"type": "boolean", "const": True},
                    "owner_override_satisfies_all_qtt_internal_requirements": {
                        "type": "boolean",
                        "const": True,
                    },
                },
            },
            "validation_summary": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "schema_validated": {"type": "boolean", "const": True},
                    "yaml_validated": {"type": "boolean", "const": True},
                    "fixture_validated": {"type": "boolean", "const": True},
                    "generated_report_validated": {"type": "boolean", "const": True},
                    "constants_schema_report_alignment_validated": {
                        "type": "boolean",
                        "const": True,
                    },
                    "forbidden_authority_terms_checked_without_scattered_blockers": {
                        "type": "boolean",
                        "const": True,
                    },
                    "changed_path_guard_validated": {"type": "boolean", "const": True},
                    "branch_context_tests_use_monkeypatch_or_explicit_simulation": {
                        "type": "boolean",
                        "const": True,
                    },
                    "os_stable_paths": {"type": "boolean", "const": True},
                    "full_gate_run": {"type": "string"},
                    "full_gate_result": {"type": "string"},
                    "generated_side_effects_restored": {"type": "string"},
                },
            },
            "validation_marker": {"type": "string", "const": c.SUCCESS_MARKER},
            "execution": {"type": "string", "const": "DISABLED"},
            "mode": {"type": "string", "const": "SOURCE_REQUIRED"},
        },
        "required": [
            "report_type",
            "report_version",
            "artifact_stem",
            "authority_class",
            "generated_at_utc",
            "generated_by_validator_tool",
            "generated_from_static_evidence_only",
            "pr_identity_resolution",
            "repo_status_preflight",
            "path_derivation_basis",
            "owner_global_override_directive",
            "internal_gate_release_contract",
            "non_owner_evidence_boundary",
            "pr142_handoff_consumption",
            "pr136_orchestration_preflight",
            "pr143k_forward_handoff",
            "source_evidence_boundary",
            "atomicrows_compatibility",
            "quantum_forward_compatibility",
            "classical_optimizer_forward_compatibility",
            "latency_hot_path_boundary",
            "no_claim_boundary",
            "forbidden_payload_boundary",
            "existing_owner_global_override_authority_consumption",
            "validation_summary",
            "validation_marker",
        ],
    }
    return schema


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    from tools.build_master_plan_section_coverage_report import load_yaml_subset

    value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a YAML object")
    return value


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _validate_no_forbidden_integrity_authority(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed = set(c.ALLOWED_INTEGRITY_FIELD_NAMES)
    for key, item in _walk(payload):
        lowered = key.lower()
        if key in allowed:
            if item is not False and key != "main_head_short_sha_as_vcs_metadata_only":
                failures.append(f"PR143_ALLOWED_INTEGRITY_NO_CLAIM_FIELD_MUST_BE_FALSE: {key}")
            continue
        if any(fragment in lowered for fragment in ("sha", "digest", "hash", "checksum")):
            failures.append(f"PR143_FORBIDDEN_INTEGRITY_AUTHORITY_FIELD: {key}")
    serialized = json.dumps(payload, sort_keys=True)
    if c.forbidden_bundle_reference_text() in serialized:
        failures.append("PR143_FORBIDDEN_ATOMICROWS_BUNDLE_SHA_PATH_REFERENCE")
    return sorted(set(failures))


def _validate_false_boundary(
    payload: Mapping[str, Any],
    section: str,
    expected: Mapping[str, bool],
) -> list[str]:
    failures: list[str] = []
    actual = payload.get(section)
    if not isinstance(actual, Mapping):
        return [f"PR143_BOUNDARY_SECTION_MISSING: {section}"]
    if dict(actual) != dict(expected):
        failures.append(f"PR143_BOUNDARY_SECTION_MISMATCH: {section}")
    for key, value in actual.items():
        if value is not False:
            failures.append(f"PR143_FORBIDDEN_AUTHORITY_TRUE: {section}.{key}")
    return sorted(set(failures))


def validate_constants_schema_alignment(schema: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    authority_enum = (
        schema.get("properties", {})
        .get("authority_class", {})
        .get("enum")
    )
    if authority_enum != list(c.AUTHORITY_CLASS_VALUES):
        failures.append("PR143_SCHEMA_AUTHORITY_CLASS_ENUM_MISMATCH")
    released_enum = (
        schema.get("properties", {})
        .get("internal_gate_release_contract", {})
        .get("properties", {})
        .get("released_internal_gate_classes", {})
        .get("items", {})
        .get("enum")
    )
    if released_enum != list(c.RELEASED_INTERNAL_GATE_CLASSES):
        failures.append("PR143_SCHEMA_RELEASED_GATE_ENUM_MISMATCH")
    preserved_enum = (
        schema.get("properties", {})
        .get("non_owner_evidence_boundary", {})
        .get("properties", {})
        .get("preserved_non_owner_evidence_classes", {})
        .get("items", {})
        .get("enum")
    )
    if preserved_enum != list(c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED):
        failures.append("PR143_SCHEMA_NON_OWNER_EVIDENCE_ENUM_MISMATCH")
    quantum_state = (
        schema.get("properties", {})
        .get("quantum_forward_compatibility", {})
        .get("properties", {})
        .get("quantum_planning_state", {})
        .get("const")
    )
    if quantum_state != c.QUANTUM_PLANNING_STATE:
        failures.append("PR143_SCHEMA_QUANTUM_STATE_MISMATCH")
    return failures


def validate_payload(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    failures = [
        f"PR143_SCHEMA_VALIDATION_FAILED: {failure}"
        for failure in validate_json_schema_subset(dict(payload), dict(schema))
    ]
    failures.extend(validate_constants_schema_alignment(schema))
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR143_AUTHORITY_CLASS_MISMATCH")
    if payload.get("generated_from_static_evidence_only") is not True:
        failures.append("PR143_NOT_STATIC_EVIDENCE_ONLY")

    release = payload.get("internal_gate_release_contract", {})
    if isinstance(release, Mapping):
        if release.get("released_internal_gate_classes") != list(c.RELEASED_INTERNAL_GATE_CLASSES):
            failures.append("PR143_RELEASED_INTERNAL_GATE_CLASSES_NOT_CONSTANT_ALIGNED")
        if release.get("released_pr142_blocked_reason_codes") != list(
            c.OWNER_GATE_CODES_RELEASED_BY_PR143
        ):
            failures.append("PR143_RELEASED_PR142_BLOCKERS_NOT_CONSTANT_ALIGNED")
        if release.get("active_owner_approval_blockers_after_pr143") != []:
            failures.append("PR143_OWNER_APPROVAL_BLOCKERS_STILL_ACTIVE")

    boundary = payload.get("non_owner_evidence_boundary", {})
    if isinstance(boundary, Mapping):
        if boundary.get("preserved_non_owner_evidence_classes") != list(
            c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED
        ):
            failures.append("PR143_PRESERVED_NON_OWNER_EVIDENCE_NOT_CONSTANT_ALIGNED")
        if boundary.get("non_owner_evidence_state_label") != c.NON_OWNER_EVIDENCE_STATE_LABEL:
            failures.append("PR143_NON_OWNER_EVIDENCE_STATE_LABEL_MISMATCH")

    quantum = payload.get("quantum_forward_compatibility", {})
    if isinstance(quantum, Mapping):
        for field in c.QUANTUM_PLANNING_ALLOWED_FIELDS:
            if quantum.get(field) is not True:
                failures.append(f"PR143_QUANTUM_PLANNING_FIELD_NOT_RELEASED: {field}")
        for field in (
            "true_quantum_backend_execution_created",
            "quantum_simulator_execution_created",
            "qaoa_execution_created",
            "vqe_execution_created",
            "annealing_execution_created",
            "qubo_solving_created",
            "ising_solving_created",
            "quantum_optimizer_input_output_created",
            "quantum_advantage_claim_created",
            "parameter_ranges_invented",
            "optimizer_defaults_invented",
        ):
            if quantum.get(field) is not False:
                failures.append(f"PR143_FORBIDDEN_QUANTUM_OUTPUT_CREATED: {field}")

    failures.extend(
        _validate_false_boundary(payload, "no_claim_boundary", c.NO_CLAIM_BOUNDARY)
    )
    failures.extend(
        _validate_false_boundary(
            payload,
            "forbidden_payload_boundary",
            c.FORBIDDEN_PAYLOAD_BOUNDARY,
        )
    )
    failures.extend(_validate_no_forbidden_integrity_authority(payload))
    return sorted(set(failures))


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--short", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        if len(line) > 2 and line[2] == " ":
            path = line[3:]
        elif len(line) > 1 and line[1] == " ":
            path = line[2:]
        else:
            path = line[3:] if len(line) > 3 else line
        paths.append(path.strip().replace("\\", "/"))
    return paths


def _is_ignored_pr143_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    tmp_dir, _tmp_glob = c.IGNORED_PR143_CHANGED_PATH_PATTERNS
    return normalized == tmp_dir or normalized.startswith(tmp_dir)


def _branch_allows_pr143_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        143,
        allow_main=False,
        allow_repair=False,
    )


def _branch_allows_pr138_mainline_context_repair_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr138_mainline_context_repair_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS
        and _branch_allows_pr138_mainline_context_repair_changed_paths(branch)
    )


def _branch_allows_pr142_changed_path_guard_compatibility_repair_changed_paths(
    branch: str,
) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS
        and _branch_allows_pr142_changed_path_guard_compatibility_repair_changed_paths(
            branch
        )
    )


def _branch_allows_pr146_generated_report_nonmutating_validation_repair_changed_paths(
    branch: str,
) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized
        in c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_CHANGED_PATHS
        and _branch_allows_pr146_generated_report_nonmutating_validation_repair_changed_paths(
            branch
        )
    )


def _branch_allows_pr148_checkpoint_currentization_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr148_checkpoint_currentization_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized
        in c.PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_CHANGED_PATHS
        and _branch_allows_pr148_checkpoint_currentization_changed_paths(branch)
    )


def _branch_allows_pr149_implementation_bridge_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 148, allow_repair=False)


def _is_pr149_implementation_bridge_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR149_IMPLEMENTATION_BRIDGE_CHANGED_PATHS
        and _branch_allows_pr149_implementation_bridge_changed_paths(branch)
    )


def _branch_allows_pr150_target_matrix_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 149, allow_repair=False)


def _is_pr150_target_matrix_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR150_TARGET_MATRIX_CHANGED_PATHS
        and _branch_allows_pr150_target_matrix_changed_paths(branch)
    )


def _branch_allows_pr151_retrieval_target_pack_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr151_retrieval_target_pack_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS
        and _branch_allows_pr151_retrieval_target_pack_changed_paths(branch)
    )


def _branch_allows_pr152_audit_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr152_audit_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in pr152_constants.PR152_AUDIT_CHANGED_PATHS
        and _branch_allows_pr152_audit_changed_paths(branch)
    )


def _is_allowed_pr143_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.ALLOWED_PR143_CHANGED_PATHS
        and _branch_allows_pr143_changed_paths(branch)
    ) or _is_pr138_mainline_context_repair_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr148_checkpoint_currentization_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr149_implementation_bridge_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr150_target_matrix_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr151_retrieval_target_pack_changed_path_for_branch(
        normalized,
        branch,
    ) or _is_pr152_audit_changed_path_for_branch(
        normalized,
        branch,
    )


def _is_allowed_pr143_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_allowed_pr143_changed_path_for_branch(path, branch_context.branch)


def _validate_changed_paths(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR143_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if _is_ignored_pr143_changed_path(normalized):
            continue
        if not _is_allowed_pr143_changed_path(normalized, repo_root):
            failures.append(f"PR143_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR143_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR143_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized.startswith(c.ROW_FAMILY_SOURCE_DIRECTORY.as_posix() + "/"):
            failures.append("PR143_ROW_FAMILY_SOURCE_MUTATION_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    schema = build_json_schema(root)
    expected_gate = build_gate(root)
    expected_report = build_report(root)
    expected_fixture = build_fixture(root)
    if expected_report != build_report(root):
        return ["PR143_OUTPUT_NOT_DETERMINISTIC"]

    failures: list[str] = []
    try:
        actual_schema = _read_json(root / c.SCHEMA_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_schema = {}
        failures.append(f"PR143_SCHEMA_INVALID: {c.SCHEMA_PATH.as_posix()}: {exc}")
    if actual_schema and actual_schema != schema:
        failures.append("PR143_SCHEMA_STALE_OR_NONDETERMINISTIC")
    if actual_schema:
        failures.extend(validate_constants_schema_alignment(actual_schema))

    try:
        actual_gate = _read_yaml(root / c.YAML_PATH)
    except (OSError, ValueError) as exc:
        actual_gate = {}
        failures.append(f"PR143_YAML_INVALID: {c.YAML_PATH.as_posix()}: {exc}")
    if actual_gate and actual_gate != expected_gate:
        failures.append("PR143_YAML_STALE_OR_NONDETERMINISTIC")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR143_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR143_REPORT_STALE_OR_NONDETERMINISTIC")

    try:
        actual_fixture = _read_json(root / c.FIXTURE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_fixture = {}
        failures.append(f"PR143_FIXTURE_INVALID: {c.FIXTURE_PATH.as_posix()}: {exc}")
    if actual_fixture and actual_fixture != expected_fixture:
        failures.append("PR143_FIXTURE_STALE_OR_NONDETERMINISTIC")

    for label, payload in (
        ("YAML", actual_gate),
        ("REPORT", actual_report),
        ("FIXTURE", actual_fixture),
    ):
        if payload:
            failures.extend(
                f"PR143_{label}_{failure}" for failure in validate_payload(payload, schema)
            )

    failures.extend(_validate_changed_paths(root))
    return sorted(set(failures))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_schema_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    schema = build_json_schema(root)
    _write_text(root / c.SCHEMA_PATH, json_dump(schema))
    return schema


def write_gate_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    gate = build_gate(root)
    _write_text(root / c.YAML_PATH, yaml_dump(gate))
    return gate


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    _write_text(root / c.REPORT_PATH, json_dump(report))
    return report


def write_fixture_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    fixture = build_fixture(root)
    _write_text(root / c.FIXTURE_PATH, json_dump(fixture))
    return fixture


def write_all_artifacts(repo_root: Path | str) -> dict[str, Any]:
    return {
        "schema": write_schema_file(repo_root),
        "gate": write_gate_file(repo_root),
        "report": write_report_file(repo_root),
        "fixture": write_fixture_file(repo_root),
    }
