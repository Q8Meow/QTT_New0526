"""Validation and artifact writers for the PR142 AtomicRows handoff gate."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    BranchContext,
    PR166_QC_BRANCH,
    current_branch_context,
    is_downstream_roadmap_branch,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
    is_validation_infrastructure_branch,
    is_validation_infrastructure_changed_path,
)
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as pr152_constants,
)

from . import constants as c
from .builder import build_fixture, build_gate, build_report, json_dump, yaml_dump


def _path_schema() -> dict[str, Any]:
    return {"type": "array", "minItems": 1, "items": {"type": "string"}}


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
    false_authority = _false_boundary_schema(c.FORBIDDEN_AUTHORITY_OUTPUT_FIELDS)
    no_claim = _false_boundary_schema(c.NO_CLAIM_FALSE_FIELDS)
    forbidden_payload = _false_boundary_schema(c.FORBIDDEN_PAYLOAD_BOUNDARY_FIELDS)
    quantum_false = _false_boundary_schema(c.QUANTUM_EXECUTION_FALSE_FIELDS)
    classical_false = _false_boundary_schema(c.CLASSICAL_OPTIMIZER_FALSE_FIELDS)

    latency = _object_schema(
        {
            "control_plane_only": {"type": "boolean", "const": True},
            "live_pretrade_dependency_created": {"type": "boolean", "const": False},
            "live_path_import_created": {"type": "boolean", "const": False},
            "runtime_service_created": {"type": "boolean", "const": False},
            "order_router_dependency_created": {"type": "boolean", "const": False},
            "no_live_path_runtime_call": {"type": "boolean", "const": True},
            "no_doc_retrieval_in_live_path": {"type": "boolean", "const": True},
            "no_quantum_call_in_live_path": {"type": "boolean", "const": True},
            "no_optimizer_call_in_live_path": {"type": "boolean", "const": True},
        },
        additional=False,
    )

    source_boundary = _object_schema(
        {
            "source_evidence_packet_consumed_if_present": {"type": "boolean"},
            "source_evidence_packet_repo_path_present": {"type": "boolean"},
            "source_evidence_packet_path": {"type": "string"},
            "owner_policy_may_authorize_retrieval_scope": {
                "type": ["boolean", "string"],
                "enum": [True, "unknown"],
            },
            "owner_policy_may_authorize_external_fact_value": {
                "type": "boolean",
                "const": False,
            },
            "source_acceptance_created": {"type": "boolean", "const": False},
            "connector_semantic_binding_created": {"type": "boolean", "const": False},
            "runtime_cash_receipt_created": {"type": "boolean", "const": False},
            "missing_accepted_source_packets_block_runtime_use": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    readiness_contract = _object_schema(
        {
            "ready_to_request_owner_review": {"type": "boolean", "const": True},
            "ready_to_prepare_future_materialization_plan": {
                "type": "boolean",
                "const": True,
            },
            "readiness_state": {"type": "string", "enum": list(c.READINESS_STATES)},
            "blocked_reason_codes": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "enum": list(c.BLOCK_REASON_CODES)},
            },
            "required_future_owner_action": {"type": "string"},
            "required_future_accepted_source_or_runtime_receipt_dependencies": _path_schema(),
            "next_pr_static_input_created": {"type": "boolean", "const": True},
            "future_materialization_still_requires_explicit_owner_approval": {
                "type": "boolean",
                "const": True,
            },
        },
        additional=False,
    )

    atomicrows_compatibility = _object_schema(
        {
            "enrichment_order_preserved": {"type": "boolean", "const": True},
            "enrichment_order": _path_schema(),
            "semantic_row_contract_preserved": {"type": "boolean", "const": True},
            "row_family_source_manifest_preserved": {"type": "boolean", "const": True},
            "field_coverage_plan_preserved": {"type": "boolean", "const": True},
            "owner_authorization_readiness_gate_preserved": {
                "type": "boolean",
                "const": True,
            },
            "value_materialization_still_blocked": {"type": "boolean", "const": True},
            "no_bundle_mutation": {"type": "boolean", "const": True},
            "no_row_family_source_mutation": {"type": "boolean", "const": True},
            "no_bundle_authority_created": {"type": "boolean", "const": True},
            "no_bundle_freeze_authority_created": {"type": "boolean", "const": True},
            "pr141_blocked_counts": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "source_evidence_blocked_count": {"type": "integer"},
                    "runtime_receipt_blocked_count": {"type": "integer"},
                    "replay_paper_evidence_blocked_count": {"type": "integer"},
                },
                "required": [
                    "source_evidence_blocked_count",
                    "runtime_receipt_blocked_count",
                    "replay_paper_evidence_blocked_count",
                ],
            },
        },
        additional=False,
    )

    quantum = _object_schema(
        {
            "quantum_forward_metadata_only": {"type": "boolean", "const": True},
            "quantum_applicability_source": _path_schema(),
            **quantum_false["properties"],
            "optimizer_parameter_value_source_status": {
                "type": "string",
                "const": "NOT_MATERIALIZED_OR_NOT_ACCEPTED",
            },
            "compatible_future_problem_forms": {
                "type": "string",
                "const": "UNKNOWN_PENDING_EVIDENCE",
            },
            "future_optimizer_compatibility_notes": _path_schema(),
            "missing_optimizer_default_policy_route": {
                "type": "string",
                "const": "BLOCK_UNTIL_ACCEPTED_EVIDENCE_OR_OWNER_POLICY",
            },
            "metadata_only_fields": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "string",
                    "enum": list(c.QUANTUM_FORWARD_METADATA_ONLY_FIELDS),
                },
            },
        },
        additional=False,
    )

    classical = _object_schema(
        {
            **classical_false["properties"],
            "deterministic_field_identity_ready": {"type": "boolean", "const": True},
            "missing_value_materialization_blocks_optimizer_use": {
                "type": "boolean",
                "const": True,
            },
            "missing_external_fact_evidence_blocks_runtime_use": {
                "type": "boolean",
                "const": True,
            },
            "missing_owner_approval_blocks_materialization": {
                "type": "boolean",
                "const": True,
            },
            "missing_replay_paper_results_blocks_live_promotion": {
                "type": "boolean",
                "const": True,
            },
            "missing_runtime_cash_receipt_blocks_exposure": {
                "type": "boolean",
                "const": True,
            },
            "metadata_only_fields": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "string",
                    "enum": list(c.CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS),
                },
            },
        },
        additional=False,
    )

    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://qtt.local/schemas/atomicrows/"
            "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.schema.json"
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
                    "evidence_derived_name_used": {"type": "boolean"},
                    "fallback_name_used": {"type": "boolean"},
                    "name_derivation_notes": {"type": "string"},
                },
                "required": [
                    "repo_current_pr",
                    "github_pr_number",
                    "roadmap_identity_inference_used",
                    "implementation_truth",
                    "evidence_derived_name_used",
                    "fallback_name_used",
                    "name_derivation_notes",
                ],
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
                "required": [
                    "local_main_verified",
                    "local_main_clean",
                    "main_head_short_sha_as_vcs_metadata_only",
                    "github_main_validation_status",
                    "github_status_claimed",
                    "branch_created_after_scope_receipt",
                ],
            },
            "pr136_orchestration_preflight": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "consumed_files": _path_schema(),
                    "alias_resolution": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "requested_alias": {"type": "string"},
                            "alias_exists": {"type": "boolean"},
                            "canonical_crosswalk_used": {"type": "string"},
                            "created_missing_alias": {
                                "type": "boolean",
                                "const": False,
                            },
                            "conflict_detected": {"type": "boolean", "const": False},
                        },
                        "required": [
                            "requested_alias",
                            "alias_exists",
                            "canonical_crosswalk_used",
                            "created_missing_alias",
                            "conflict_detected",
                        ],
                    },
                    "route_triage_alignment": {"type": "object"},
                    "sequence_alignment": {"type": "object"},
                    "dependency_alignment": {"type": "object"},
                    "launch_readiness_domain_alignment": {"type": "object"},
                    "market_specific_alignment": {"type": "object"},
                    "command_action_alignment": {"type": "array", "minItems": 1},
                    "quantum_atomicrows_optimization_readiness_alignment": {
                        "type": "object"
                    },
                    "agent_launch_orchestration_alignment": {"type": "object"},
                    "replay_paper_live_transition_boundary": {"type": "object"},
                    "pr136_planning_authority_only": {
                        "type": "boolean",
                        "const": True,
                    },
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
                },
                "required": [
                    "consumed_files",
                    "alias_resolution",
                    "route_triage_alignment",
                    "sequence_alignment",
                    "dependency_alignment",
                    "launch_readiness_domain_alignment",
                    "market_specific_alignment",
                    "command_action_alignment",
                    "quantum_atomicrows_optimization_readiness_alignment",
                    "agent_launch_orchestration_alignment",
                    "replay_paper_live_transition_boundary",
                    "pr136_planning_authority_only",
                    "pr136_does_not_authorize_materialization",
                    "pr136_does_not_authorize_live_trading",
                    "pr136_does_not_authorize_quantum_execution",
                    "pr136_does_not_authorize_day1_launch",
                ],
            },
            "upstream_atomicrows_evidence": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "consumed_files": _path_schema(),
                    "pr137r_bundle_reconciliation_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr137l_latency_hot_path_boundary_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr138_semantic_row_contract_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr138_semantic_field_inventory_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr139_row_family_source_manifest_currentization_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr140_semantic_field_coverage_enrichment_plan_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                    "pr141_owner_authorization_readiness_gate_consumed": {
                        "type": "boolean",
                        "const": True,
                    },
                },
                "required": [
                    "consumed_files",
                    "pr137r_bundle_reconciliation_consumed",
                    "pr137l_latency_hot_path_boundary_consumed",
                    "pr138_semantic_row_contract_consumed",
                    "pr138_semantic_field_inventory_consumed",
                    "pr139_row_family_source_manifest_currentization_consumed",
                    "pr140_semantic_field_coverage_enrichment_plan_consumed",
                    "pr141_owner_authorization_readiness_gate_consumed",
                ],
            },
            "pr141_downstream_handoff_consumption": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "upstream_report_path": {"type": "string"},
                    "upstream_yaml_path": {"type": "string"},
                    "downstream_handoff_contract_detected": {
                        "type": "boolean",
                        "const": True,
                    },
                    "downstream_handoff_contract": {"type": "object"},
                    "yaml_downstream_handoff_contract": {"type": "object"},
                    "downstream_handoff_scope": {"type": "string"},
                    "downstream_handoff_allowed_for_this_pr": {
                        "type": "boolean",
                        "const": True,
                    },
                    "exact_future_step_prepared": {"type": "string"},
                    "owner_approval_inferred": {"type": "boolean", "const": False},
                    "owner_approval_receipt_created": {
                        "type": "boolean",
                        "const": False,
                    },
                    "materialization_permission_created": {
                        "type": "boolean",
                        "const": False,
                    },
                    "semantic_values_materialized": {"type": "boolean", "const": False},
                    "bundle_mutation_created": {"type": "boolean", "const": False},
                    "row_family_source_mutation_created": {
                        "type": "boolean",
                        "const": False,
                    },
                },
                "required": [
                    "upstream_report_path",
                    "upstream_yaml_path",
                    "downstream_handoff_contract_detected",
                    "downstream_handoff_contract",
                    "yaml_downstream_handoff_contract",
                    "downstream_handoff_scope",
                    "downstream_handoff_allowed_for_this_pr",
                    "exact_future_step_prepared",
                    "owner_approval_inferred",
                    "owner_approval_receipt_created",
                    "materialization_permission_created",
                    "semantic_values_materialized",
                    "bundle_mutation_created",
                    "row_family_source_mutation_created",
                ],
            },
            "static_handoff_readiness_contract": readiness_contract,
            "source_evidence_boundary": source_boundary,
            "atomicrows_compatibility": atomicrows_compatibility,
            "quantum_forward_compatibility": quantum,
            "classical_optimizer_forward_compatibility": classical,
            "latency_hot_path_boundary": latency,
            "no_claim_boundary": no_claim,
            "forbidden_authority_output_boundary": false_authority,
            "forbidden_payload_boundary": forbidden_payload,
            "path_conflict_resolution": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "conflicts_detected": {"type": "boolean", "const": False},
                    "path_conflict_resolution": {"type": "string"},
                },
                "required": ["conflicts_detected", "path_conflict_resolution"],
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
                    "changed_path_guard_validated": {
                        "type": "boolean",
                        "const": True,
                    },
                    "branch_context_tests_use_monkeypatch_or_explicit_simulation": {
                        "type": "boolean",
                        "const": True,
                    },
                    "os_stable_paths": {"type": "boolean", "const": True},
                    "full_gate_run": {"type": "string"},
                    "full_gate_result": {"type": "string"},
                    "generated_side_effects_restored": {"type": "string"},
                },
                "required": [
                    "schema_validated",
                    "yaml_validated",
                    "fixture_validated",
                    "generated_report_validated",
                    "constants_schema_report_alignment_validated",
                    "forbidden_authority_terms_checked_without_scattered_blockers",
                    "changed_path_guard_validated",
                    "branch_context_tests_use_monkeypatch_or_explicit_simulation",
                    "os_stable_paths",
                    "full_gate_run",
                    "full_gate_result",
                    "generated_side_effects_restored",
                ],
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
            "pr136_orchestration_preflight",
            "upstream_atomicrows_evidence",
            "pr141_downstream_handoff_consumption",
            "static_handoff_readiness_contract",
            "source_evidence_boundary",
            "atomicrows_compatibility",
            "quantum_forward_compatibility",
            "classical_optimizer_forward_compatibility",
            "latency_hot_path_boundary",
            "no_claim_boundary",
            "forbidden_authority_output_boundary",
            "forbidden_payload_boundary",
            "path_conflict_resolution",
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
    for key, _item in _walk(payload):
        lowered = key.lower()
        if key in c.ALLOWED_VCS_METADATA_FIELD_NAMES:
            continue
        if any(fragment in lowered for fragment in ("sha", "digest", "hash", "checksum")):
            failures.append(f"PR142_FORBIDDEN_INTEGRITY_AUTHORITY_FIELD: {key}")
    serialized = json.dumps(payload, sort_keys=True)
    if c.forbidden_bundle_reference_text() in serialized:
        failures.append("PR142_FORBIDDEN_ATOMICROWS_BUNDLE_REFERENCE")
    return sorted(set(failures))


def _validate_false_boundary(
    payload: Mapping[str, Any],
    section: str,
    expected: Mapping[str, bool],
) -> list[str]:
    failures: list[str] = []
    actual = payload.get(section)
    if not isinstance(actual, Mapping):
        return [f"PR142_BOUNDARY_SECTION_MISSING: {section}"]
    if dict(actual) != dict(expected):
        failures.append(f"PR142_BOUNDARY_SECTION_MISMATCH: {section}")
    for key, value in actual.items():
        if value is not False:
            failures.append(f"PR142_FORBIDDEN_AUTHORITY_TRUE: {section}.{key}")
    return sorted(set(failures))


def validate_constants_schema_alignment(schema: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    authority_enum = (
        schema.get("properties", {})
        .get("authority_class", {})
        .get("enum")
    )
    if authority_enum != list(c.AUTHORITY_CLASS_VALUES):
        failures.append("PR142_SCHEMA_AUTHORITY_CLASS_ENUM_MISMATCH")
    reason_enum = (
        schema.get("properties", {})
        .get("static_handoff_readiness_contract", {})
        .get("properties", {})
        .get("blocked_reason_codes", {})
        .get("items", {})
        .get("enum")
    )
    if reason_enum != list(c.BLOCK_REASON_CODES):
        failures.append("PR142_SCHEMA_BLOCK_REASON_ENUM_MISMATCH")
    quantum_enum = (
        schema.get("properties", {})
        .get("quantum_forward_compatibility", {})
        .get("properties", {})
        .get("metadata_only_fields", {})
        .get("items", {})
        .get("enum")
    )
    if quantum_enum != list(c.QUANTUM_FORWARD_METADATA_ONLY_FIELDS):
        failures.append("PR142_SCHEMA_QUANTUM_METADATA_ENUM_MISMATCH")
    classical_enum = (
        schema.get("properties", {})
        .get("classical_optimizer_forward_compatibility", {})
        .get("properties", {})
        .get("metadata_only_fields", {})
        .get("items", {})
        .get("enum")
    )
    if classical_enum != list(c.CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS):
        failures.append("PR142_SCHEMA_CLASSICAL_METADATA_ENUM_MISMATCH")
    return failures


def validate_payload(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    failures = [
        f"PR142_SCHEMA_VALIDATION_FAILED: {failure}"
        for failure in validate_json_schema_subset(dict(payload), dict(schema))
    ]
    failures.extend(validate_constants_schema_alignment(schema))
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR142_AUTHORITY_CLASS_MISMATCH")
    if payload.get("generated_from_static_evidence_only") is not True:
        failures.append("PR142_NOT_STATIC_EVIDENCE_ONLY")
    failures.extend(
        _validate_false_boundary(
            payload,
            "no_claim_boundary",
            c.NO_CLAIM_BOUNDARY,
        )
    )
    failures.extend(
        _validate_false_boundary(
            payload,
            "forbidden_authority_output_boundary",
            c.FORBIDDEN_AUTHORITY_OUTPUT_BOUNDARY,
        )
    )
    failures.extend(
        _validate_false_boundary(
            payload,
            "forbidden_payload_boundary",
            c.FORBIDDEN_PAYLOAD_BOUNDARY,
        )
    )
    failures.extend(_validate_no_forbidden_integrity_authority(payload))

    handoff = payload.get("pr141_downstream_handoff_consumption", {})
    if isinstance(handoff, Mapping):
        upstream = handoff.get("downstream_handoff_contract", {})
        yaml_handoff = handoff.get("yaml_downstream_handoff_contract", {})
        if dict(upstream) != dict(yaml_handoff):
            failures.append("PR142_PR141_REPORT_YAML_HANDOFF_MISMATCH")
        for key in (
            "pr141_authorizes_materialization",
            "pr141_authorizes_bundle_mutation",
            "pr141_authorizes_row_family_source_mutation",
            "pr141_authorizes_source_acceptance",
            "pr141_authorizes_connector_binding",
            "pr141_authorizes_replay_execution",
            "pr141_authorizes_paper_execution",
            "pr141_authorizes_live_order_authority",
            "pr141_authorizes_quantum_backend_execution",
            "pr141_authorizes_final_readiness",
        ):
            if isinstance(upstream, Mapping) and upstream.get(key) is not False:
                failures.append(f"PR142_PR141_FORBIDDEN_HANDOFF_TRUE: {key}")
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
        normalized = path.strip().replace("\\", "/")
        if " -> " in normalized:
            normalized = normalized.rsplit(" -> ", 1)[1]
        paths.append(normalized)
    return paths


def _is_ignored_pr142_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    tmp_dir, _tmp_glob = c.IGNORED_PR142_CHANGED_PATH_PATTERNS
    return normalized == tmp_dir or normalized.startswith(tmp_dir)


def _branch_allows_pr142_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        142,
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
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


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
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


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


def _is_pr166_qc_replay_paper_changed_path_for_validation_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return is_validation_infrastructure_branch(
        branch
    ) and is_explicit_downstream_repair_changed_path(PR166_QC_BRANCH, normalized)


def _is_allowed_pr142_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.ALLOWED_PR142_CHANGED_PATHS
        and _branch_allows_pr142_changed_paths(branch)
    ) or _is_pr138_mainline_context_repair_changed_path_for_branch(
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
    ) or is_explicit_downstream_repair_changed_path(
        branch,
        normalized,
    ) or _is_pr166_qc_replay_paper_changed_path_for_validation_branch(
        normalized,
        branch,
    ) or is_validation_infrastructure_changed_path(
        branch,
        normalized,
    )


def _is_allowed_pr142_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_allowed_pr142_changed_path_for_branch(path, branch_context.branch)


def _validate_changed_paths(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR142_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if _is_ignored_pr142_changed_path(normalized):
            continue
        if not _is_allowed_pr142_changed_path(normalized, repo_root):
            failures.append(f"PR142_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR142_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR142_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized.startswith(c.ROW_FAMILY_SOURCE_DIRECTORY.as_posix() + "/"):
            failures.append("PR142_ROW_FAMILY_SOURCE_MUTATION_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    schema = build_json_schema(root)
    expected_gate = build_gate(root)
    expected_report = build_report(root)
    expected_fixture = build_fixture(root)
    if expected_report != build_report(root):
        return ["PR142_OUTPUT_NOT_DETERMINISTIC"]

    failures: list[str] = []
    try:
        actual_schema = _read_json(root / c.SCHEMA_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_schema = {}
        failures.append(f"PR142_SCHEMA_INVALID: {c.SCHEMA_PATH.as_posix()}: {exc}")
    if actual_schema and actual_schema != schema:
        failures.append("PR142_SCHEMA_STALE_OR_NONDETERMINISTIC")
    if actual_schema:
        failures.extend(validate_constants_schema_alignment(actual_schema))

    try:
        actual_gate = _read_yaml(root / c.YAML_PATH)
    except (OSError, ValueError) as exc:
        actual_gate = {}
        failures.append(f"PR142_YAML_INVALID: {c.YAML_PATH.as_posix()}: {exc}")
    if actual_gate and actual_gate != expected_gate:
        failures.append("PR142_YAML_STALE_OR_NONDETERMINISTIC")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR142_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR142_REPORT_STALE_OR_NONDETERMINISTIC")

    try:
        actual_fixture = _read_json(root / c.FIXTURE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_fixture = {}
        failures.append(f"PR142_FIXTURE_INVALID: {c.FIXTURE_PATH.as_posix()}: {exc}")
    if actual_fixture and actual_fixture != expected_fixture:
        failures.append("PR142_FIXTURE_STALE_OR_NONDETERMINISTIC")

    for label, payload in (
        ("YAML", actual_gate),
        ("REPORT", actual_report),
        ("FIXTURE", actual_fixture),
    ):
        if payload:
            failures.extend(
                f"PR142_{label}_{failure}" for failure in validate_payload(payload, schema)
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
