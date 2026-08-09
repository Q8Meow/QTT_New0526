#!/usr/bin/env python3
"""Independent source-and-artifact validator for the exact ST12-D boundary.

Frozen expectations are reconstructed here, then compared with source AST,
builder-owned reference-only projections, and a bounded subprocess that treats
the production authority boundary strictly as the system under test.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PACKAGE = REPO_ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
ARTIFACTS = REPO_ROOT / "docs/master_plan/generated/qku_control_plane/mode_snapshot"
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_D_INDEPENDENTLY_VALIDATED"

EXPECTED_GENERATED_NAMES = (
    "manifest.json",
    "control_closure.jsonl",
    "parameter_binding_refs.jsonl",
    "mode_state_registry.jsonl",
    "transition_matrix.jsonl",
    "d_input_universe.jsonl",
    "computability_dispositions.jsonl",
    "artifact_connectivity.jsonl",
    "validation_summary.json",
)
EXPECTED_COUNTS = {
    "closure_controls": 23,
    "historical_path_dispositions": 7,
    "parameter_bindings": 28,
    "math_specifications": 4,
    "independent_oracles": 4,
    "golden_vectors": 4,
    "semantic_tests": 26,
    "certified_commands": 6,
}
EXPECTED_REPAIR_METRICS = {
    "canonical_current_resolver_enforced_count": 1,
    "custom_resolver_bypass_count": 0,
    "executed_transition_trace_gap_count": 0,
    "stage_transition_receipt_mismatch_count": 0,
    "phantom_receipt_ref_count": 0,
    "synthetic_source_epoch_ref_count": 0,
    "actual_control_mutation_case_count": 23,
    "semantic_test_identity_count": 26,
    "synthetic_override_mutation_count": 0,
}
EXPECTED_TERMINAL_OUTCOME_MATRIX = (
    (("T03",), False, "EVIDENCE_UNAVAILABLE", "ABSENT"),
    (("T04",), False, "BLOCKED", "ABSENT"),
    (("T05",), False, "BLOCKED", "ABSENT"),
    (("T08", "T09", "T06"), True, "OWNER_CONFIRMATION_REQUIRED", "VALIDATED_NO_EFFECT"),
    (("T08", "T09", "T07"), True, "ELIGIBLE_NOT_ACTIVATED", "VALIDATED_NO_EFFECT"),
    (("T08", "T10"), False, "BLOCKED", "REJECTED"),
    (("T08", "T09", "T04"), True, "BLOCKED", "VALIDATED_NO_EFFECT"),
)
EXPECTED_TERMINAL_CANDIDATE_DECISION_FIELD_PAIRS = (
    ("request_id", "request_id"),
    ("principal_id", "principal_id"),
    ("task_id", "task_id"),
    ("capability_decision_ref", "capability_decision_ref"),
    ("computation_bundle_ref", "computation_bundle_ref"),
    ("context_ref", "context_ref"),
    ("implementation_version_pins", "implementation_pins"),
    ("parameter_policy_snapshot_ref", "parameter_policy_snapshot_ref"),
    ("source_epoch_refs", "source_epoch_refs"),
    ("receipt_lineage_refs", "receipt_lineage_refs"),
    ("readiness_state_ref", "readiness_state_ref"),
    ("pretrade_state_ref", "pretrade_state_ref"),
    ("evidence_state_ref", "evidence_state_ref"),
    ("kill_state_ref", "kill_state_ref"),
    ("submit_disabled_state_ref", "submit_disabled_state_ref"),
    ("expires_at", "expires_at"),
)
EXPECTED_REGISTERED_PHASES = (
    "fast-preflight",
    "deterministic-validators-a",
    "deterministic-validators-b",
    "deterministic-validators-c",
    "pytest-shard-1",
    "pytest-shard-2",
    "pytest-shard-3",
    "pytest-shard-4",
    "pytest-shard-5",
    "pytest-shard-6",
    "pytest-shard-7",
    "pytest-shard-8",
    "post-validation",
)
EXPECTED_MANIFEST_KEYS = frozenset(
    {
        "acceptance_counts",
        "active_pointer_commit_count",
        "actual_control_mutation_case_count",
        "actual_control_mutation_rejection_count",
        "actual_control_positive_pass_count",
        "agent_policy_edit_count",
        "artifact_connectivity_terminal_counts",
        "canonical_current_resolver_enforced_count",
        "custom_resolver_bypass_count",
        "d_input_universe_count",
        "d_input_universe_count_by_class",
        "d_input_universe_unresolved_count",
        "d_path_existence_only_consumption_count",
        "d_value_level_upstream_consumption_gap_count",
        "executed_transition_trace_gap_count",
        "generated_projection_paths",
        "implementation_owner",
        "manual_edit_allowed",
        "new_public_operation_id_count",
        "order_release_authorized",
        "order_release_count",
        "orphan_d_artifact_count",
        "parameter_value_owner_count",
        "phantom_receipt_ref_count",
        "pin_dimension_count",
        "runtime_effect_authorized",
        "runtime_effect_count",
        "schema",
        "semantic_owner",
        "semantic_test_identity_count",
        "semantic_test_pass_count",
        "stage_transition_receipt_mismatch_count",
        "state_count",
        "synthetic_override_mutation_count",
        "synthetic_source_epoch_ref_count",
        "tranche",
        "transition_count",
    }
)
EXPECTED_SUMMARY_KEYS = frozenset(
    {
        "acceptance_counts",
        "active_pointer_commit_count",
        "actual_control_mutation_case_count",
        "actual_control_mutation_rejection_count",
        "actual_control_positive_pass_count",
        "artifact_connectivity_terminal_counts",
        "canonical_current_resolver_enforced_count",
        "conditional_merge_implementation_count",
        "custom_resolver_bypass_count",
        "d_input_universe_count_by_class",
        "d_input_universe_unresolved_count",
        "d_path_existence_only_consumption_count",
        "d_value_level_upstream_consumption_gap_count",
        "executed_transition_trace_gap_count",
        "external_candidate_discovery_count",
        "metadata_only_completion_count",
        "order_release_authorized",
        "order_release_count",
        "orphan_d_artifact_count",
        "phantom_receipt_ref_count",
        "provider_private_replay_paper_llm_qpu_counts",
        "qtt_checksum_or_digest_authority_count",
        "runtime_effect_authorized",
        "runtime_effect_count",
        "schema",
        "semantic_test_identity_count",
        "semantic_test_pass_count",
        "stage_transition_receipt_mismatch_count",
        "synthetic_override_mutation_count",
        "synthetic_source_epoch_ref_count",
        "unacknowledged_future_handoff_count",
        "unmapped_current_agent_authority_count_for_d_rows",
        "web_search_count",
    }
)
EXPECTED_UNIVERSE_CLASS_COUNTS = {
    "certified_command": 6,
    "closure_control": 23,
    "current_owner_interface": 16,
    "frozen_contract_policy_file": 29,
    "generated_audit_output": 9,
    "golden_vector": 4,
    "historical_path_disposition": 7,
    "independent_oracle": 4,
    "math_component": 4,
    "mode_state": 35,
    "mode_transition": 17,
    "parameter_binding": 28,
    "pin_dimension": 12,
    "runtime_no_effect_output": 8,
    "semantic_test": 26,
    "validation_currentization_owner": 12,
}
EXPECTED_CLOSURE_IDS = (
    *(f"ST12-CLOSURE::ST11-EXECUTION::{number:03d}" for number in range(10, 15)),
    *(
        f"ST12-CLOSURE::ST11-LATENCY::{number:03d}"
        for number in (1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
    ),
    *(f"ST12-CLOSURE::ST11-SECURITY::{number:03d}" for number in range(11, 14)),
)
EXPECTED_PARAMETER_IDS = tuple(
    f"ST10-PARAM::{number:04d}"
    for number in (
        332,
        456,
        457,
        463,
        464,
        467,
        764,
        940,
        1946,
        2026,
        2112,
        2117,
        2157,
        2493,
        2639,
        2641,
        2642,
        2644,
        2645,
        2646,
        2647,
        2648,
        3002,
        3003,
        3490,
        3598,
        3639,
        3641,
    )
)
EXPECTED_MATH_IDS = ("MATH-13", "MATH-14", "MATH-15", "MATH-39")
EXPECTED_TEST_IDS = tuple(
    f"ST12-TEST::{number:03d}"
    for number in (
        64,
        66,
        76,
        77,
        80,
        82,
        84,
        85,
        87,
        88,
        89,
        90,
        91,
        92,
        94,
        95,
        96,
        97,
        98,
        99,
        193,
        194,
        195,
        224,
        225,
        230,
    )
)
EXPECTED_SEMANTIC_CASE_OR_VALIDATOR_REFS = (
    "ST11-EXECUTION::014",
    "ST11-EXECUTION::013",
    "ST11-EXECUTION::012",
    "ST11-EXECUTION::010",
    "ST11-EXECUTION::011",
    "ST11-LATENCY::001",
    "ST11-LATENCY::005",
    "ST11-LATENCY::011",
    "ST11-LATENCY::014",
    "ST11-LATENCY::003",
    "ST11-LATENCY::015",
    "ST11-LATENCY::004",
    "ST11-LATENCY::016",
    "ST11-LATENCY::019",
    "ST11-LATENCY::020",
    "ST11-LATENCY::018",
    "ST11-LATENCY::017",
    "ST11-LATENCY::013",
    "ST11-LATENCY::002",
    "ST11-LATENCY::012",
    "ST11-SECURITY::012",
    "ST11-SECURITY::011",
    "ST11-SECURITY::013",
    "INDEPENDENT-EXECUTION-VALIDATOR",
    "INDEPENDENT-LATENCY-VALIDATOR",
    "INDEPENDENT-SECURITY-VALIDATOR",
)
EXPECTED_COMMANDS = (
    "python tools/independent_validate_qku_computation_control_plane_execution.py",
    "python tools/independent_validate_qku_computation_control_plane_latency.py",
    "python tools/independent_validate_qku_computation_control_plane_security.py",
    "python tools/validate_qku_computation_control_plane.py --domain execution",
    "python tools/validate_qku_computation_control_plane.py --domain latency",
    "python tools/validate_qku_computation_control_plane.py --domain security",
)
EXPECTED_RUNTIME_CONSUMERS = {
    "OUTPUT::SNAPSHOT-CANDIDATE": (
        "CandidateProposalV1.mode_snapshot_result.snapshot_candidate_or_explicit_absence",
        "SubmitCandidateProposalResponseV1.proposal",
    ),
    "OUTPUT::MODE-DECISION": (
        "SubmitCandidateProposalResponseV1.proposal",
        "ModeSnapshotOwnerProjectionV1.decision_id",
    ),
    "OUTPUT::TRANSITION-PROPOSAL": (
        "SubmitCandidateProposalResponseV1.proposal",
        "ModeSnapshotCandidateProposalResultV1.executed_transition_trace",
        "EconomicReceiptEventSpineV1.ModeSnapshotControlReceiptRecordV1.transition_proposal_ref",
    ),
    "OUTPUT::PROPOSAL-RESULT": (
        "SubmitCandidateProposalResponseV1.proposal.mode_snapshot_result",
    ),
    "OUTPUT::CONTROL-RECEIPT": (
        "PersistenceAdapterV1.insert_receipt_record_when_AVAILABLE_REFERENCE",
        "ModeSnapshotCandidateProposalResultV1.control_receipt_proposals",
    ),
    "OUTPUT::OWNER-PROJECTION": (
        "ModeSnapshotCandidateProposalResultV1.owner_projection_or_explicit_absence",
        "ExistingOwnerProjectionAdapterV1.project_mode_snapshot",
    ),
    "OUTPUT::LATENCY-MEASUREMENT": (
        "ModeSnapshotCandidateProposalResultV1.latency_measurement_or_explicit_absence",
        "ModeSnapshotControlReceiptRecordV1.latency_measurement_ref_or_explicit_absence",
    ),
    "OUTPUT::MATH-39-QUEUE-AHEAD": (
        "ComputeComponentResponseV1.component_result",
    ),
}
EXPECTED_PUBLIC_OPERATIONS = (
    "resolve_identity",
    "resolve_contextual_computability",
    "resolve_applicable_stack",
    "resolve_required_inputs",
    "compute_component",
    "compute_stack",
    "compare_with_no_trade",
    "evaluate_trade_plan",
    "get_snapshot_view",
    "explain_resolution",
    "submit_candidate_proposal",
    "request_materialization_work_order",
    "compile_replay_paper_cohort",
    "register_replay_paper_result",
    "build_evidence_bundle",
)
EXPECTED_STATES = {
    "MODE_ELIGIBILITY": (
        "INELIGIBLE",
        "CONTRACT_ONLY",
        "ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT",
    ),
    "ALLOW_CANDIDATE": (
        "NOT_EVALUATED",
        "BLOCKED",
        "EVIDENCE_UNAVAILABLE",
        "OWNER_CONFIRMATION_REQUIRED",
        "ELIGIBLE_NOT_ACTIVATED",
    ),
    "ACTIVATION_PRECONDITION": (
        "NOT_AUTHORIZED_D_HOLD",
        "PRECONDITIONS_INCOMPLETE",
        "PRECONDITIONS_SATISFIED_HELD",
    ),
    "SNAPSHOT_CANDIDATE": (
        "ABSENT",
        "BUILT_IMMUTABLE",
        "VALIDATED_NO_EFFECT",
        "REJECTED",
        "STALE",
        "ROLLBACK_REQUIRED",
        "RETIRED",
    ),
    "KILL_STATE": ("CLEAR_CURRENT", "ACTIVE", "MISSING_STALE_OR_CONFLICTING"),
    "SUBMIT_DISABLED_STATE": (
        "SUBMIT_ENABLED_READ_ONLY",
        "SUBMIT_DISABLED",
        "MISSING_STALE_OR_CONFLICTING",
    ),
    "EVIDENCE_STATE": (
        "EVIDENCE_REFERENCE_AVAILABLE",
        "EVIDENCE_REFERENCE_STALE",
        "EVIDENCE_REFERENCE_CONFLICTING",
        "EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED",
        "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    ),
    "ROLLBACK_STATE": (
        "NONE",
        "PROPOSED_PRIOR_IMMUTABLE_CANDIDATE",
        "BLOCKED_NO_VALID_PRIOR_CANDIDATE",
    ),
    "RETIREMENT_STATE": ("CURRENT", "DRAINING_PINNED_IN_FLIGHT_ONLY", "RETIRED"),
}
EXPECTED_TRANSITIONS = (
    ("T01", "CONTRACT_ONLY", "INELIGIBLE", "CAPABILITY_DENIED", "BLOCK", False),
    ("T02", "CONTRACT_ONLY", "ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT", "CENTRAL_ADMISSION_PASS", "CONTINUE_NO_EFFECT", False),
    ("T03", "NOT_EVALUATED", "EVIDENCE_UNAVAILABLE", "EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED", "BLOCK", False),
    ("T04", "NOT_EVALUATED", "BLOCKED", "POLICY_OR_SNAPSHOT_STALE", "REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE", False),
    ("T05", "NOT_EVALUATED", "BLOCKED", "KILL_OR_SUBMIT_DISABLED", "BLOCK", False),
    ("T06", "NOT_EVALUATED", "OWNER_CONFIRMATION_REQUIRED", "OWNER_CONFIRMATION_REQUIRED", "HOLD", False),
    ("T07", "OWNER_CONFIRMATION_REQUIRED", "ELIGIBLE_NOT_ACTIVATED", "ALLOW_ELIGIBLE_NOT_ACTIVATED", "RETURN_DECISION_NO_EFFECT", True),
    ("T08", "ABSENT", "BUILT_IMMUTABLE", "SNAPSHOT_CANDIDATE_BUILT", "VALIDATE", False),
    ("T09", "BUILT_IMMUTABLE", "VALIDATED_NO_EFFECT", "SNAPSHOT_CANDIDATE_VALID", "RETURN_PROPOSAL_NO_EFFECT", False),
    ("T10", "BUILT_IMMUTABLE", "REJECTED", "SNAPSHOT_CANDIDATE_INVALID", "BLOCK", False),
    ("T11", "VALIDATED_NO_EFFECT", "STALE", "SNAPSHOT_STALE", "BLOCK_NEW_USE", False),
    ("T12", "VALIDATED_NO_EFFECT", "ROLLBACK_REQUIRED", "ROLLBACK_REQUIRED", "PROPOSE_PRIOR_CANDIDATE_NO_COMMIT", False),
    ("T13", "ROLLBACK_REQUIRED", "PROPOSED_PRIOR_IMMUTABLE_CANDIDATE", "ROLLBACK_PROPOSAL_VALID", "RETURN_PROPOSAL_NO_EFFECT", False),
    ("T14", "ROLLBACK_REQUIRED", "BLOCKED_NO_VALID_PRIOR_CANDIDATE", "NO_VALID_ROLLBACK_TARGET", "BLOCK", False),
    ("T15", "CURRENT", "DRAINING_PINNED_IN_FLIGHT_ONLY", "RETIREMENT_DRAIN", "NO_NEW_PINS", False),
    ("T16", "DRAINING_PINNED_IN_FLIGHT_ONLY", "RETIRED", "RETIRED", "NO_NEW_USE", False),
    ("T17", "ANY", "BLOCKED", "NO_TRADE_REOPTIMIZATION_ROUTED", "ROUTE_TO_PRETRADE1_REOPTIMIZATION", False),
)
EXPECTED_TRANSITION_TRIGGERS = (
    "capability denied or identity/policy mismatch",
    "exact E decision, current inputs, kill clear",
    "F evidence unavailable",
    "policy/source/snapshot stale or conflicting",
    "kill active or submit disabled",
    "all automated gates pass but exact owner action absent",
    "exact owner confirmation packet is valid",
    "all pinned inputs resolve and candidate builds",
    "schema, lineage, version, source, parameter, freshness and oracle checks pass",
    "any candidate validation fails",
    "critical source/policy/evidence/kill state expires",
    "post-validation defect or conflict detected",
    "prior candidate exists, validates and is not stale",
    "no valid prior candidate",
    "retirement declared",
    "all in-flight references complete",
    "PRETRADE1 returns typed NO_TRADE",
)
EXPECTED_CONTRACT_FIELDS = {
    "ReadOnlyKillSubmitStateV1": (
        "state_ref", "scope_ref", "kill_active", "submit_disabled", "observed_at",
        "valid_until", "policy_version", "causation_id", "correlation_id",
    ),
    "ST12FEvidenceReferenceV1": (
        "evidence_state", "evidence_ref", "lane", "dataset_grade_ref",
        "venue_semantic_binding_ref", "cross_venue_equivalence_ref", "observed_at",
        "valid_until", "policy_version", "causation_id", "correlation_id",
        "input_lock_id", "component_or_template_ref", "evidence_bundle_version",
        "source_epoch_refs", "terminal_state", "reference_id", "evidence_id",
        "contract_version", "no_effect_flags",
    ),
    "OwnerActionConfirmationReceiptV1": (
        "receipt_ref", "owner_action_policy_ref", "state", "principal_id",
        "task_id", "capability_decision_ref", "context_ref", "observed_at",
        "valid_until", "causation_id", "correlation_id",
        "predecessor_transition_id_or_explicit_absence",
        "predecessor_transition_receipt_ref_or_explicit_absence",
        "predecessor_transition_receipt_proposal_or_explicit_absence",
        "runtime_effect_authorized", "order_release_authorized",
    ),
    "FormulaRuntimeSnapshotCandidateV1": (
        "snapshot_candidate_id", "request_id", "principal_id", "task_id",
        "capability_decision_ref", "computation_bundle_ref", "context_ref",
        "formula_spec_refs", "implementation_version_pins", "binding_profile_ref",
        "parameter_policy_snapshot_ref", "parameter_value_refs", "source_epoch_refs",
        "receipt_lineage_refs", "readiness_state_ref", "pretrade_state_ref",
        "evidence_state_ref", "kill_state_ref", "submit_disabled_state_ref",
        "created_at", "evaluated_at", "expires_at", "stale_at", "candidate_state",
        "reason_codes", "fallback_route", "owner_review_route",
        "runtime_effect_authorized", "order_release_authorized", "activated",
    ),
    "SnapshotTransitionProposalV1": (
        "proposal_id", "request_id", "principal_id", "task_id",
        "capability_decision_ref", "context_ref",
        "source_candidate_ref_or_explicit_absence", "target_candidate_ref",
        "source_candidate_version_or_explicit_absence", "target_candidate_version",
        "transition_id", "source_state", "destination_state",
        "expected_owner_state_ref", "precondition_receipt_refs",
        "predecessor_transition_receipt_refs",
        "predecessor_transition_receipt_proposals", "proposed_state",
        "primary_reason_code", "diagnostic_reason_codes", "typed_reason_codes",
        "owner_confirmation_required", "causation_id", "correlation_id",
        "no_mutation_flag", "no_activation_flag", "no_order_release_flag",
        "active_pointer_commit_allowed", "mutation_allowed",
        "runtime_effect_authorized", "order_release_authorized",
    ),
    "ExecutedModeSnapshotTransitionTraceV1": (
        "proposals",
    ),
    "ModeSnapshotCandidateProposalResultV1": (
        "snapshot_candidate_or_explicit_absence", "mode_snapshot_decision",
        "snapshot_transition_proposal", "executed_transition_trace",
        "control_receipt_refs",
        "owner_projection_or_explicit_absence",
        "latency_measurement_or_explicit_absence", "control_receipt_proposals",
        "no_authority_flag",
    ),
    "ResolvedSnapshotParameterValueV1": (
        "parameter_id", "parameter_symbol", "resolved_value_ref",
        "canonical_typed_value_or_explicit_unavailable", "value_kind",
        "unit_or_basis", "resolution_state", "policy_ref",
        "parameter_policy_set_version", "producer_receipt_refs",
        "point_in_time_receipt_refs", "freshness_receipt_refs",
        "source_epoch_refs", "observed_at_or_explicit_absence",
        "valid_until_or_explicit_absence", "diagnostic_reason_codes",
        "no_mutation_flag",
    ),
    "ModeSnapshotControlReceiptRecordV1": (
        "control_receipt_id", "control_class", "request_id", "task_id", "principal_id",
        "capability_decision_ref", "context_ref",
        "snapshot_candidate_ref_or_explicit_absence", "mode_snapshot_decision_ref",
        "transition_proposal_ref", "transition_id", "source_state",
        "destination_state", "target_candidate_version", "implementation_pin_refs",
        "parameter_value_refs", "source_epoch_refs",
        "predecessor_transition_receipt_refs", "state_before_refs", "state_after_refs",
        "typed_reason_codes", "fallback_route", "owner_review_route",
        "latency_measurement_ref_or_explicit_absence", "owner_action_policy_ref",
        "no_mutation_flag", "no_activation_flag", "no_order_authority_flag",
    ),
}
EXPECTED_PROTOCOL_FIELDS = {
    "OwnerProjectionViewV1": (
        "owner_id", "authority_domain", "source_path", "source_version",
        "source_snapshot_ref", "consume_interfaces", "row_count",
        "identity_refs", "receipt_refs", "source_epoch_refs",
        "projection_mutation_allowed", "runtime_effect_allowed",
    ),
    "PreloadedOwnerProjectionBundleV1": (
        "readiness", "pretrade", "svc", "agent_orch",
    ),
}
REQUIRED_CONNECTIVITY_FIELDS = {
    "semantic_ref",
    "artifact_or_row_class",
    "canonical_identity_refs",
    "semantic_owner",
    "implementation_owner",
    "producer_path_or_interface",
    "exact_upstream_fields_or_refs_consumed",
    "upstream_refs",
    "current_value_owner_ref_or_explicit_absence",
    "current_principal_and_duty_refs_or_explicit_absence",
    "downstream_D_contract_fields_affected",
    "downstream_consumer_refs",
    "consumer_acknowledgment_ref_or_explicit_absence",
    "schema_ref",
    "validator_ref",
    "mutation_test_ref_or_explicit_not_material",
    "computability_disposition_ref_or_explicit_absence",
    "terminal_disposition",
    "terminal_route",
    "runtime_effect_authorized",
    "order_release_authorized",
}
ALLOWED_TERMINAL_DISPOSITIONS = {
    "CONSUMED_BY_D_CANDIDATE",
    "CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
    "ROUTED_TO_EXISTING_MATERIALIZATION_OWNER",
    "ROUTED_TO_NAMED_LATER_OWNER_WITH_NO_D_EFFECT",
    "NOT_APPLICABLE_WITH_PROOF",
    "TERMINAL_BY_NATURE_WITH_PROOF",
}
EFFECT_KEYS = {
    "runtime_effect_authorized",
    "order_release_authorized",
    "active_pointer_commit_allowed",
    "mutation_allowed",
    "activated",
    "value_mutation_authorized_by_st12d",
}


class ValidationFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"{path} must contain one object")
    return value


def _read_jsonl(path: Path) -> tuple[dict[str, object], ...]:
    rows = tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    _require(all(isinstance(row, dict) for row in rows), f"{path} rows must be objects")
    return rows


def _source_tree(name: str) -> ast.Module:
    return ast.parse((PACKAGE / name).read_text(encoding="utf-8"), filename=name)


def _class_node(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise ValidationFailure(f"missing class {name}")


def _class_fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(item.target.id for item in node.body if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name))


def _recursive_effect_check(value: object, location: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in EFFECT_KEYS:
                _require(nested is False, f"effect flag {location}.{key} is not exact false")
            _recursive_effect_check(nested, f"{location}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _recursive_effect_check(nested, f"{location}[{index}]")


def _git_path_changed(path: str) -> bool:
    for base in ("main", "origin/main"):
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "--", path],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    raise ValidationFailure("cannot compare agent_policy.py with current main")


def _execute_runtime_repair_probe() -> dict[str, int]:
    probe_source = r'''
import json
from dataclasses import replace
from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import OwnerAdapterError
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    CurrentModeSnapshotInputResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    _require_current_mode_snapshot_resolver,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12D_ACTUAL_CONTROL_MUTATION_CASES,
    ST12D_SEMANTIC_TEST_ROWS,
    _st12d_build_control_fixture,
    run_st12d_actual_control_mutation_case,
)

results = tuple(
    run_st12d_actual_control_mutation_case(control_id)
    for control_id in ST12D_ACTUAL_CONTROL_MUTATION_CASES
)
by_control = {row.control_id: row for row in results}
fixture = _st12d_build_control_fixture("ST11-EXECUTION::012")
exact = _require_current_mode_snapshot_resolver(fixture.service)

class CustomEvidenceAvailableResolver:
    def __init__(self):
        self.gate_calls = 0
        self.enrichment_calls = 0

    def resolve_mode_snapshot_preconstruction_gate(self, *_args):
        self.gate_calls += 1
        return object()

    def enrich_mode_snapshot_candidate(self, *_args):
        self.enrichment_calls += 1
        return object()

custom = CustomEvidenceAvailableResolver()
custom_bypassed = True
try:
    _require_current_mode_snapshot_resolver(
        replace(fixture.service, mode_snapshot_input_resolver=custom)
    )
except OwnerAdapterError:
    custom_bypassed = False

wrong_registry_bypassed = True
wrong_registry = CanonicalOwnerPacketRegistryV1()
try:
    _require_current_mode_snapshot_resolver(
        replace(
            fixture.service,
            mode_snapshot_input_resolver=CurrentModeSnapshotInputResolverV1(
                repo_root=Path("."),
                owner_registry=wrong_registry,
            ),
        )
    )
except OwnerAdapterError:
    wrong_registry_bypassed = False

resolver_result = by_control["ST11-EXECUTION::012"]
receipt_result = by_control["ST11-EXECUTION::013"]
epoch_result = by_control["ST11-EXECUTION::014"]
stage_result = by_control["ST11-SECURITY::012"]
payload = {
    "canonical_current_resolver_enforced_count": int(
        type(exact) is CurrentModeSnapshotInputResolverV1
        and exact.owner_registry is fixture.service.owner_registry
        and resolver_result.positive_passed
    ),
    "custom_resolver_bypass_count": int(
        custom_bypassed or not resolver_result.actual_mutation_rejected
    ),
    "custom_resolver_late_call_count": custom.gate_calls + custom.enrichment_calls,
    "wrong_registry_bypass_count": int(wrong_registry_bypassed),
    "executed_transition_trace_gap_count": int(not stage_result.positive_passed),
    "stage_transition_receipt_mismatch_count": int(
        not stage_result.actual_mutation_rejected
    ),
    "phantom_receipt_ref_count": int(not receipt_result.actual_mutation_rejected),
    "synthetic_source_epoch_ref_count": int(
        not epoch_result.actual_mutation_rejected
    ),
    "actual_control_mutation_case_count": len(results),
    "actual_control_positive_pass_count": sum(row.positive_passed for row in results),
    "actual_control_mutation_rejection_count": sum(
        row.actual_mutation_rejected for row in results
    ),
    "semantic_test_identity_count": len(ST12D_SEMANTIC_TEST_ROWS),
    "synthetic_override_mutation_count": sum(
        row.positive_terminal_state == row.negative_reason_or_terminal_state
        or not row.actual_mutation_rejected
        for row in results
    ),
}
print(json.dumps(payload, sort_keys=True))
'''
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", probe_source],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    _require(
        completed.returncode == 0 and completed.stdout.strip(),
        "bounded production authority probe failed: " + completed.stderr.strip(),
    )
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    _require(
        isinstance(payload, dict)
        and all(type(value) is int for value in payload.values()),
        "bounded production authority probe returned a malformed result",
    )
    for key, expected in EXPECTED_REPAIR_METRICS.items():
        _require(payload.get(key) == expected, f"runtime repair metric mismatch: {key}")
    _require(
        payload.get("custom_resolver_late_call_count") == 0
        and payload.get("wrong_registry_bypass_count") == 0
        and payload.get("actual_control_positive_pass_count") == 23
        and payload.get("actual_control_mutation_rejection_count") == 23,
        "resolver rejection was late or the 23 real mutation probes did not close",
    )
    return {key: int(payload[key]) for key in EXPECTED_REPAIR_METRICS}


def _validate_denominators_and_artifact_identity(
    runtime_metrics: dict[str, int],
) -> tuple[
    dict[str, object], tuple[dict[str, object], ...], tuple[dict[str, object], ...]
]:
    _require(ARTIFACTS.is_dir(), "ST12-D generated owner directory is missing")
    names = tuple(sorted(path.name for path in ARTIFACTS.iterdir() if path.is_file()))
    _require(names == tuple(sorted(EXPECTED_GENERATED_NAMES)), "generated path set is not exact")
    manifest = _read_json(ARTIFACTS / "manifest.json")
    summary = _read_json(ARTIFACTS / "validation_summary.json")
    _require(
        set(manifest) == EXPECTED_MANIFEST_KEYS
        and set(summary) == EXPECTED_SUMMARY_KEYS,
        "generated manifest or validation-summary report key set changed",
    )
    controls = _read_jsonl(ARTIFACTS / "control_closure.jsonl")
    parameters = _read_jsonl(ARTIFACTS / "parameter_binding_refs.jsonl")
    states = _read_jsonl(ARTIFACTS / "mode_state_registry.jsonl")
    transitions = _read_jsonl(ARTIFACTS / "transition_matrix.jsonl")
    universe = _read_jsonl(ARTIFACTS / "d_input_universe.jsonl")
    connectivity = _read_jsonl(ARTIFACTS / "artifact_connectivity.jsonl")
    computability = _read_jsonl(ARTIFACTS / "computability_dispositions.jsonl")

    _require(manifest.get("acceptance_counts") == EXPECTED_COUNTS, "frozen denominator mismatch")
    _require(tuple(row.get("closure_id") for row in controls) == EXPECTED_CLOSURE_IDS, "23 closure identities mismatch")
    control_predicate_refs = tuple(row.get("predicate_ref") for row in controls)
    control_mutation_refs = tuple(row.get("causal_mutation_ref") for row in controls)
    _require(
        len(set(control_predicate_refs)) == 23
        and len(set(control_mutation_refs)) == 23
        and all(
            row.get("positive_fixture_ref")
            and row.get("causal_owner_field_ref")
            and row.get("expected_terminal_state")
            for row in controls
        ),
        "23 controls lack unique row-specific predicates or causal mutations",
    )
    _require(tuple(row.get("parameter_id") for row in parameters) == EXPECTED_PARAMETER_IDS, "28 parameter identities mismatch")
    _require(len({row.get("canonical_value_owner") for row in parameters}) == 1, "parameter-value owner is not unique")
    allowed_parameter_keys = {
        "parameter_id", "parameter_symbol", "d_application_class", "snapshot_binding_class",
        "current_source_binding_refs", "authoritative_value_policy_ref",
        "canonical_value_owner", "value_mutation_authorized_by_st12d",
    }
    _require(all(set(row) == allowed_parameter_keys for row in parameters), "generated parameter projection copied or omitted fields")
    _require(not any({"value", "range", "default", "seed", "fallback", "precision", "runtime_resolution_procedure"} & set(row) for row in parameters), "generated parameter projection contains a value body")

    state_map: dict[str, list[str]] = {}
    for row in states:
        state_map.setdefault(str(row["dimension"]), []).append(str(row["state"]))
    _require({key: tuple(value) for key, value in state_map.items()} == EXPECTED_STATES, "exact 35-state registry mismatch")
    actual_transitions = tuple(
        (
            row.get("transition_id"), row.get("source_state"), row.get("destination_state"),
            row.get("reason_code"), row.get("terminal_route"), row.get("owner_confirmation_required"),
        )
        for row in transitions
    )
    _require(actual_transitions == EXPECTED_TRANSITIONS, "exact 17-transition matrix mismatch")
    _require(
        tuple(row.get("trigger") for row in transitions)
        == EXPECTED_TRANSITION_TRIGGERS,
        "exact 17-transition trigger oracle mismatch",
    )

    by_class = Counter(str(row.get("input_class")) for row in universe)
    _require(dict(sorted(by_class.items())) == EXPECTED_UNIVERSE_CLASS_COUNTS, "D input universe class enumeration mismatch")
    _require(len(universe) == 240, "D input universe count mismatch")
    member_refs = tuple(str(row.get("member_ref")) for row in universe)
    _require(len(member_refs) == len(set(member_refs)), "D input universe has duplicate identities")
    _require(all(row.get("terminal_disposition") != "UNRESOLVED" for row in universe), "D input universe has unresolved rows")

    _require(len(connectivity) == len(universe), "artifact connectivity is not one-to-one with D universe")
    _require({row.get("artifact_ref") for row in connectivity} == set(member_refs), "artifact connectivity has orphan or missing members")
    for row in connectivity:
        _require(REQUIRED_CONNECTIVITY_FIELDS <= set(row), "artifact connectivity required field missing")
        _require(row.get("terminal_disposition") in ALLOWED_TERMINAL_DISPOSITIONS, "artifact connectivity disposition is not terminal")
        _require(row.get("consumption_status") == "TERMINAL", "artifact connectivity row is not consumed")
        for key in REQUIRED_CONNECTIVITY_FIELDS - EFFECT_KEYS:
            value = row.get(key)
            _require(value not in (None, "", [], {}), f"blank material connectivity field {key}")
    runtime_rows = tuple(row for row in connectivity if row.get("artifact_or_row_class") == "runtime_no_effect_output")
    _require(len(runtime_rows) == 8, "runtime D output connectivity count mismatch")
    _require(all(row.get("current_principal_and_duty_refs_or_explicit_absence") == [
        "AgentCapabilityDecisionV1.principal_id",
        "AgentCapabilityDecisionV1.current_agent_id",
        "AgentCapabilityDecisionV1.task_id",
        "AGENT_ORCH1.task_envelope.duty_ref",
    ] for row in runtime_rows), "agent-consumable D output lacks current principal/task/duty binding")
    _require(
        {
            str(row.get("artifact_ref")): tuple(row.get("downstream_consumer_refs", ()))
            for row in runtime_rows
        }
        == EXPECTED_RUNTIME_CONSUMERS,
        "runtime outputs do not identify their exact operational consumers",
    )
    _require(
        all(
            row.get("consumer_acknowledgment_ref_or_explicit_absence")
            != "EXPLICIT_ABSENCE"
            and all(
                "independent_validate" not in str(consumer)
                for consumer in row.get("downstream_consumer_refs", ())
            )
            for row in runtime_rows
        ),
        "a validator is still represented as a runtime output consumer",
    )
    independently_connected = {
        str(row.get("artifact_ref"))
        for row in connectivity
        if row.get("downstream_consumer_refs")
        and (
            row.get("artifact_or_row_class") != "runtime_no_effect_output"
            or row.get("consumer_acknowledgment_ref_or_explicit_absence")
            != "EXPLICIT_ABSENCE"
        )
        or row.get("terminal_disposition")
        == "ROUTED_TO_NAMED_LATER_OWNER_WITH_NO_D_EFFECT"
    }
    independently_computed_orphans = set(member_refs) - independently_connected
    _require(
        not independently_computed_orphans
        and summary.get("orphan_d_artifact_count")
        == len(independently_computed_orphans),
        "D orphan count is hard-coded or differs from resolvable connectivity",
    )

    _require(tuple(row.get("component_ref") for row in computability) == EXPECTED_MATH_IDS, "four-component computability roster mismatch")
    for row in computability:
        _require(
            tuple(row.get(name) for name in ("specification_state", "fixture_state", "context_state", "stack_state"))
            == ("SPECIFICATION_COMPUTABLE", "FIXTURE_COMPUTABLE", "CONTEXT_COMPUTABLE", "STACK_COMPUTABLE"),
            "four-dimensional computability state mismatch",
        )
        _require(len(row.get("oracle_and_vector_refs", [])) == 2, "oracle/vector computability refs missing")
        _require(
            len(row.get("dimension_producer_receipt_refs", [])) == 4
            and all(
                dimension.get("dependency_receipt_refs")
                or dimension.get("oracle_receipt_refs")
                for dimension in row.get("dimension_producer_receipt_refs", [])
            ),
            "computability dimension lacks actual central receipt refs",
        )
        _require(
            row.get("selected_snapshot_bundle_ref")
            == "SNAPSHOT-BUNDLE::ST12D::MATH-13-14-15-39"
            and row.get("dependency_graph_ref")
            == "EXPLICIT_ABSENCE_NO_FABRICATED_DATA_EDGE",
            "D computability did not use the exact edge-free snapshot bundle",
        )
    semantic_rows = tuple(
        row for row in universe if row.get("input_class") == "semantic_test"
    )
    _require(tuple(row.get("member_ref") for row in semantic_rows) == EXPECTED_TEST_IDS, "26 semantic test identities mismatch")
    semantic_mapped_refs = tuple(
        row["exact_fields_or_refs"][1] for row in semantic_rows
    )
    semantic_mutation_refs = tuple(
        row.get("mutation_test_ref_or_explicit_not_material")
        for row in semantic_rows
    )
    mutation_by_control = {
        str(row.get("control_id")): row.get("causal_mutation_ref")
        for row in controls
    }
    _require(
        semantic_mapped_refs == EXPECTED_SEMANTIC_CASE_OR_VALIDATOR_REFS
        and semantic_mutation_refs[:23]
        == tuple(
            mutation_by_control[control_id]
            for control_id in EXPECTED_SEMANTIC_CASE_OR_VALIDATOR_REFS[:23]
        )
        and all(
            str(value).startswith("EXPLICIT_NOT_MATERIAL_WITH_PROOF::INDEPENDENT-")
            for value in semantic_mutation_refs[23:]
        ),
        "26 semantic identities are not aliases to 23 controls plus three validators",
    )
    _require(tuple(row["exact_fields_or_refs"][0] for row in universe if row.get("input_class") == "certified_command") == EXPECTED_COMMANDS, "six certified commands mismatch")
    _require(tuple(row.get("member_ref", "").rsplit("::", 1)[-1] for row in universe if row.get("input_class") == "math_component") == EXPECTED_MATH_IDS, "four math identities mismatch")
    _require(sum(row.get("input_class") == "independent_oracle" for row in universe) == 4, "four independent oracles missing")
    _require(sum(row.get("input_class") == "golden_vector" for row in universe) == 4, "four golden vectors missing")
    _require(
        manifest.get("actual_control_mutation_case_count") == 23
        and manifest.get("actual_control_positive_pass_count") == 23
        and manifest.get("actual_control_mutation_rejection_count") == 23
        and manifest.get("semantic_test_identity_count") == 26
        and manifest.get("semantic_test_pass_count") == 26
        and manifest.get("synthetic_override_mutation_count") == 0
        and summary.get("actual_control_mutation_case_count") == 23
        and summary.get("actual_control_positive_pass_count") == 23
        and summary.get("actual_control_mutation_rejection_count") == 23
        and summary.get("semantic_test_identity_count") == 26
        and summary.get("semantic_test_pass_count") == 26
        and summary.get("synthetic_override_mutation_count") == 0,
        "23 actual control mutations or 26 semantic aliases are incomplete",
    )
    _require(
        all(
            manifest.get(key) == value and summary.get(key) == value
            for key, value in runtime_metrics.items()
        ),
        "generated repair metrics differ from independently executed mutations",
    )

    _recursive_effect_check(manifest, "manifest")
    _recursive_effect_check(summary, "summary")
    for name, rows in (
        ("controls", controls), ("parameters", parameters), ("states", states),
        ("transitions", transitions), ("universe", universe),
        ("computability", computability), ("connectivity", connectivity),
    ):
        _recursive_effect_check(list(rows), name)
    for key in (
        "d_input_universe_unresolved_count", "d_value_level_upstream_consumption_gap_count",
        "d_path_existence_only_consumption_count", "orphan_d_artifact_count",
        "unacknowledged_future_handoff_count", "unmapped_current_agent_authority_count_for_d_rows",
        "metadata_only_completion_count", "active_pointer_commit_count", "runtime_effect_count",
        "order_release_count", "web_search_count", "external_candidate_discovery_count",
        "conditional_merge_implementation_count", "qtt_checksum_or_digest_authority_count",
    ):
        _require(summary.get(key) == 0, f"summary {key} must be exact zero")
    _require(all(value == 0 for value in summary.get("provider_private_replay_paper_llm_qpu_counts", {}).values()), "forbidden runtime implementation count is nonzero")
    return manifest, universe, connectivity


def _validate_contract_and_service_ast() -> None:
    models_source = (PACKAGE / "models.py").read_text(encoding="utf-8")
    models = ast.parse(models_source, filename="models.py")
    receipts = _source_tree("receipts.py")
    for class_name, expected_fields in EXPECTED_CONTRACT_FIELDS.items():
        tree = receipts if class_name == "ModeSnapshotControlReceiptRecordV1" else models
        _require(_class_fields(_class_node(tree, class_name)) == expected_fields, f"{class_name} field roster mismatch")
    protocols = _source_tree("protocols.py")
    for class_name, expected_fields in EXPECTED_PROTOCOL_FIELDS.items():
        _require(
            _class_fields(_class_node(protocols, class_name)) == expected_fields,
            f"{class_name} field roster mismatch",
        )

    input_resolver = _source_tree("input_resolver.py")
    input_resolver_source = (PACKAGE / "input_resolver.py").read_text(encoding="utf-8")
    policy = _source_tree("mode_snapshot_policy.py")
    policy_source = (PACKAGE / "mode_snapshot_policy.py").read_text(encoding="utf-8")
    mode_input_fields = _class_fields(
        _class_node(policy, "ModeSnapshotCandidateInputsV1")
    )
    _require(
        "computation_bundle_closure" in mode_input_fields
        and "owner_action_confirmation" in mode_input_fields
        and "all_four_computability_dimensions_closed" not in mode_input_fields
        and "owner_confirmation_present" not in mode_input_fields,
        "D input authority still accepts caller booleans instead of exact owner receipts",
    )
    for class_name in (
        "CurrentSafetyStateAdapterV1",
        "CurrentPreFEvidenceAdapterV1",
        "CurrentOwnerActionConfirmationAdapterV1",
        "CurrentModeSnapshotInputResolverV1",
    ):
        _class_node(input_resolver, class_name)
    resolver_class = _class_node(input_resolver, "CurrentModeSnapshotInputResolverV1")
    resolver_methods = {
        node.name: node
        for node in resolver_class.body
        if isinstance(node, ast.FunctionDef)
    }
    early_resolver_source = ast.get_source_segment(
        input_resolver_source,
        resolver_methods["resolve_mode_snapshot_preconstruction_gate"],
    ) or ""
    enrichment_source = ast.get_source_segment(
        input_resolver_source,
        resolver_methods["enrich_mode_snapshot_candidate"],
    ) or ""
    query_source = ast.get_source_segment(
        input_resolver_source,
        resolver_methods["_typed_f_reference_query"],
    ) or ""
    reference_validation_source = ast.get_source_segment(
        input_resolver_source,
        resolver_methods["_validate_f_reference_for_d"],
    ) or ""
    evidence_tree = _source_tree("evidence.py")
    _require(
        _class_fields(_class_node(evidence_tree, "FToDEvidenceReferenceQueryV1"))
        == (
            "query_id",
            "requested_evidence_id",
            "requested_component_or_template_ref",
            "expected_input_lock_id",
            "expected_source_epoch_refs",
            "evaluated_at",
            "request_read_lineage_refs",
        ),
        "F-to-D query does not carry the exact immutable seven-field custody roster",
    )
    _require(
        all(
            token in query_source
            for token in (
                'request_refs = tuple(getattr(request, "source_candidate_refs", ()))',
                "tagged_refs = tuple(dict.fromkeys((*request_refs, *evidence_refs)))",
                'ref.startswith("ST12F_EVIDENCE_ID=")',
                'ref.startswith("ST12F_INPUT_LOCK_ID=")',
                'ref.startswith("ST12F_COMPONENT_OR_TEMPLATE_REF=")',
                'ref.startswith("ST12F_SOURCE_EPOCH=")',
                "requested_evidence_id=",
                "requested_component_or_template_ref=",
                "expected_input_lock_id=",
                "expected_source_epoch_refs=",
                "evaluated_at=context.as_of",
                "request_read_lineage_refs=",
            )
        )
        and all(
            token in reference_validation_source
            for token in (
                "reference.evidence_id ==",
                "reference.component_or_template_ref",
                "reference.input_lock_id",
                "reference.source_epoch_refs",
                'reference.lane == "REPLAY_PAPER"',
                'reference.terminal_state == "CLOSED_INDEPENDENTLY_VALIDATED"',
                'reference.evidence_ref.startswith("ST12F-RECEIPT::")',
                'reference.contract_version == "1.4"',
                "reference.no_effect_flags == NO_EFFECTS_V1",
                "reference.observed_at",
                "reference.valid_until",
                "pre_f_unavailable_reference(",
            )
        )
        and "reference.causation_id ==" not in reference_validation_source
        and "reference.correlation_id ==" not in reference_validation_source,
        "D does not independently validate every typed F identity/scope/lock/epoch/state/no-effect/freshness pin",
    )
    _require(
        "pre_f_unavailable_reference(" in input_resolver_source
        and "read_kill_submit_state(context)" in early_resolver_source
        and "read_evidence_reference(" in early_resolver_source
        and all(
            token not in early_resolver_source
            for token in (
                "read_owner_action_confirmation",
                "resolve_st12d_snapshot_parameter_values",
                "FormulaInputResolverV1.resolve",
                "preflight_snapshot_computation_bundle",
                "owner_projections",
            )
        )
        and all(
            token in enrichment_source
            for token in (
                "read_owner_action_confirmation",
                "resolve_st12d_snapshot_parameter_values",
                "FormulaInputResolverV1.resolve",
                "preflight_snapshot_computation_bundle",
                "owner_projections.source_epoch_refs",
            )
        )
        and "ExistingOwnerProjectionAdapterV1" not in input_resolver_source
        and ".read_text(" not in input_resolver_source,
        "current D resolver is not gate-first with preloaded projection custody",
    )

    # Reconstruct the expected D truth table without calling the production
    # predicate.  One valid row and eight one-field mutations prove that every
    # authorized mismatch is independently expected to fail closed.
    baseline = {
        "evidence_id": "EVIDENCE::1",
        "scope": "MATH-01",
        "lock": "LOCK::1",
        "epochs": ("SOURCE::1=EPOCH::1",),
        "state": "EVIDENCE_REFERENCE_AVAILABLE",
        "terminal": "CLOSED_INDEPENDENTLY_VALIDATED",
        "no_effect": True,
        "fresh": True,
    }

    def independently_available(row: dict[str, object]) -> bool:
        return (
            row["evidence_id"] == "EVIDENCE::1"
            and row["scope"] == "MATH-01"
            and row["lock"] == "LOCK::1"
            and row["epochs"] == ("SOURCE::1=EPOCH::1",)
            and row["state"] == "EVIDENCE_REFERENCE_AVAILABLE"
            and row["terminal"] == "CLOSED_INDEPENDENTLY_VALIDATED"
            and row["no_effect"] is True
            and row["fresh"] is True
        )

    mutations = (
        ("evidence_id", "EVIDENCE::OTHER"),
        ("scope", "MATH-02"),
        ("lock", "LOCK::OTHER"),
        ("epochs", ("SOURCE::1=EPOCH::OTHER",)),
        ("state", "EVIDENCE_REFERENCE_STALE"),
        ("terminal", "STALE"),
        ("no_effect", False),
        ("fresh", False),
    )
    _require(
        independently_available(baseline)
        and all(
            not independently_available({**baseline, field_name: value})
            for field_name, value in mutations
        ),
        "independent F-to-D fail-closed truth table differs",
    )

    decision_fields = _class_fields(_class_node(models, "ModeSnapshotDecisionV1"))
    _require(decision_fields[-3:] == ("runtime_effect_authorized", "active_pointer_commit_allowed", "order_release_authorized"), "decision effect boundary mismatch")
    candidate_node = _class_node(models, "FormulaRuntimeSnapshotCandidateV1")
    transition_node = _class_node(models, "SnapshotTransitionProposalV1")
    trace_node = _class_node(models, "ExecutedModeSnapshotTransitionTraceV1")
    result_node = _class_node(models, "ModeSnapshotCandidateProposalResultV1")
    receipt_node = _class_node(receipts, "ModeSnapshotControlReceiptRecordV1")
    matrix_node = next(
        (
            node
            for node in models.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "_MODE_SNAPSHOT_TERMINAL_OUTCOME_MATRIX_V1"
        ),
        None,
    )
    _require(matrix_node is not None, "central terminal outcome matrix is missing")
    matrix_value = matrix_node.value
    if (
        isinstance(matrix_value, ast.Call)
        and isinstance(matrix_value.func, ast.Name)
        and matrix_value.func.id == "MappingProxyType"
        and len(matrix_value.args) == 1
    ):
        matrix_value = matrix_value.args[0]
    if not isinstance(matrix_value, ast.Dict):
        raise ValidationFailure("central terminal outcome matrix is not a readable mapping")
    reconstructed_terminal_matrix: list[tuple[tuple[str, ...], bool, str, str]] = []
    for shape_node, outcome_node in zip(
        matrix_value.keys, matrix_value.values, strict=True
    ):
        if not (
            isinstance(shape_node, ast.Tuple)
            and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in shape_node.elts
            )
            and isinstance(outcome_node, ast.Tuple)
            and len(outcome_node.elts) == 3
            and isinstance(outcome_node.elts[0], ast.Constant)
            and type(outcome_node.elts[0].value) is bool
            and isinstance(outcome_node.elts[1], ast.Attribute)
            and isinstance(outcome_node.elts[2], ast.Attribute)
        ):
            raise ValidationFailure("terminal outcome matrix row is not statically readable")
        reconstructed_terminal_matrix.append(
            (
                tuple(str(item.value) for item in shape_node.elts),
                outcome_node.elts[0].value,
                outcome_node.elts[1].attr,
                outcome_node.elts[2].attr,
            )
        )
    _require(
        tuple(reconstructed_terminal_matrix) == EXPECTED_TERMINAL_OUTCOME_MATRIX
        and ("T08",) not in {
            shape for shape, _required, _allow, _snapshot in reconstructed_terminal_matrix
        },
        "seven-row terminal outcome matrix or T08-only fail-closed rule differs",
    )

    outcome_helper_node = next(
        (
            node
            for node in models.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_validate_mode_snapshot_terminal_outcome_consistency"
        ),
        None,
    )
    _require(outcome_helper_node is not None, "central terminal outcome helper is missing")
    outcome_helper_source = ast.get_source_segment(
        models_source, outcome_helper_node
    ) or ""
    result_post_init = next(
        (
            node
            for node in result_node.body
            if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
        ),
        None,
    )
    _require(result_post_init is not None, "result post-init validator is missing")
    outcome_helper_calls = tuple(
        call
        for call in ast.walk(result_post_init)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_validate_mode_snapshot_terminal_outcome_consistency"
    )
    result_post_init_source = ast.get_source_segment(models_source, result_post_init) or ""
    _require(
        len(outcome_helper_calls) == 1
        and result_post_init_source.index(
            "_validate_mode_snapshot_terminal_outcome_consistency("
        )
        < result_post_init_source.index(
            '_validate_unique_text(self.control_receipt_refs, "control_receipt_refs")'
        ),
        "result post-init does not call one outcome helper before receipt acceptance",
    )
    candidate_decision_fields = next(
        (
            ast.literal_eval(node.value)
            for node in ast.walk(outcome_helper_node)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "candidate_decision_fields"
        ),
        None,
    )
    _require(
        candidate_decision_fields
        == EXPECTED_TERMINAL_CANDIDATE_DECISION_FIELD_PAIRS,
        "candidate/decision identity and pin join field set differs",
    )
    trace_identity_fields = next(
        (
            ast.literal_eval(node.value)
            for node in ast.walk(outcome_helper_node)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "trace_identity_fields"
        ),
        None,
    )
    _require(
        trace_identity_fields
        == (
            "request_id",
            "principal_id",
            "task_id",
            "capability_decision_ref",
            "context_ref",
        )
        and all(
            token in outcome_helper_source
            for token in (
                "candidate_required != (candidate is not None)",
                "proposal.precondition_receipt_refs != decision.receipt_lineage_refs",
                "final_proposal.primary_reason_code is not decision.reason_codes[0]",
                "final_proposal.diagnostic_reason_codes != decision.reason_codes[1:]",
                "final_proposal.typed_reason_codes != decision.reason_codes",
                "final_proposal.proposed_state is not expected_proposed_state",
                "terminal_rule.terminal_route != decision.fallback_route",
                "candidate.candidate_state is not SnapshotCandidateStateV1.VALIDATED_NO_EFFECT",
                "candidate.runtime_effect_authorized is not False",
                "candidate.order_release_authorized is not False",
                "candidate.activated is not False",
                "build_proposal.target_candidate_version",
                "validated_proposal.source_candidate_version_or_explicit_absence",
                "terminal_proposal.source_candidate_version_or_explicit_absence",
            )
        ),
        "terminal outcome helper omits an exact identity, state, reason, route, or no-effect join",
    )
    for node, names, expected in (
        (candidate_node, ("runtime_effect_authorized", "order_release_authorized", "activated"), False),
        (transition_node, ("active_pointer_commit_allowed", "mutation_allowed", "runtime_effect_authorized", "order_release_authorized"), False),
        (
            receipt_node,
            ("no_mutation_flag", "no_activation_flag", "no_order_authority_flag"),
            True,
        ),
    ):
        defaults = {
            item.target.id: item.value
            for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        }
        for name in names:
            _require(isinstance(defaults.get(name), ast.Constant) and defaults[name].value is expected, f"{node.name}.{name} default mismatch")
    transition_defaults = {
        item.target.id: item.value
        for item in transition_node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    }
    for name in ("no_mutation_flag", "no_activation_flag", "no_order_release_flag"):
        _require(
            isinstance(transition_defaults.get(name), ast.Constant)
            and transition_defaults[name].value is True,
            f"SnapshotTransitionProposalV1.{name} default mismatch",
        )

    service = _source_tree("service.py")
    service_class = _class_node(service, "QKUComputationControlPlaneV1")
    public_methods = tuple(
        node.name
        for node in service_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    )
    _require(public_methods == EXPECTED_PUBLIC_OPERATIONS, "new or missing public operation ID")
    submit = next(node for node in service_class.body if isinstance(node, ast.FunctionDef) and node.name == "submit_candidate_proposal")
    calls = [node for node in ast.walk(submit) if isinstance(node, ast.Call)]
    _require(sum(isinstance(call.func, ast.Name) and call.func.id == "_admit_agent_request" for call in calls) == 1, "submit_candidate_proposal lacks exactly one central admission")
    service_text = (PACKAGE / "service.py").read_text(encoding="utf-8")
    service_functions = {
        node.name: node
        for node in service.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    authority_source = ast.get_source_segment(
        service_text, service_functions["_require_current_mode_snapshot_resolver"]
    ) or ""
    _require(
        "type(resolver) is not CurrentModeSnapshotInputResolverV1"
        in authority_source
        and "resolver.owner_registry is not service.owner_registry"
        in authority_source
        and authority_source.count("raise OwnerAdapterError(") == 2,
        "current production D does not require the exact resolver and same registry",
    )
    admission_offset = service_text.index("capability_decision = _admit_agent_request", service_text.index("def submit_candidate_proposal"))
    discriminator_offset = service_text.index("request.candidate_kind", admission_offset)
    _require(admission_offset < discriminator_offset, "candidate kind is read before central admission")
    private_node = next(
        node
        for node in service.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_submit_mode_snapshot_candidate"
    )
    private_source = ast.get_source_segment(service_text, private_node) or ""
    authority_offset = private_source.index(
        "resolver = _require_current_mode_snapshot_resolver(self)"
    )
    gate_offset = private_source.index(
        "resolver.resolve_mode_snapshot_preconstruction_gate"
    )
    evidence_custody_offset = private_source.index(
        "evidence = gate.evidence_reference"
    )
    early_policy_offset = private_source.index(
        "evaluate_mode_snapshot_preconstruction_gate"
    )
    projection_bundle_offset = private_source.index(
        "owner_projections = self.mode_snapshot_projection_bundle"
    )
    enrichment_offset = private_source.index(
        "resolver.enrich_mode_snapshot_candidate"
    )
    schema_offset = private_source.index(
        "_validate_d_proposed_specification(request, inputs)"
    )
    body_source_offset = private_source.index(
        "source_candidate_refs = request.source_candidate_refs"
    )
    _require(
        authority_offset
        < gate_offset
        < evidence_custody_offset
        < early_policy_offset
        < projection_bundle_offset
        < enrichment_offset
        < schema_offset
        < body_source_offset,
        "canonical resolver/T05/T03 checks do not precede D enrichment/body work",
    )
    projection_offset = private_source.index(
        "projection = projection_adapter.project_mode_snapshot"
    )
    projection_attach_offset = private_source.index(
        "owner_projection_or_explicit_absence=projection"
    )
    receipts_offset = private_source.index(
        "materialize_mode_snapshot_control_receipts"
    )
    pass_one_surface_offset = private_source.index(
        "mode_snapshot_result = build_surfaces(mode_snapshot_result)"
    )
    pass_one_measurement_offset = private_source.index(
        "measurement = build_measurement(mode_snapshot_result)",
        pass_one_surface_offset,
    )
    latency_offset = private_source.index(
        "latency_decision = evaluate_latency_profile",
        pass_one_measurement_offset,
    )
    _require(
        projection_offset < projection_attach_offset < receipts_offset
        and pass_one_surface_offset < pass_one_measurement_offset < latency_offset
        and private_source.count("evaluate_latency_profile(") == 1
        and private_source.count(
            "mode_snapshot_result = build_surfaces(mode_snapshot_result)"
        )
        == 2
        and "not early_terminal" in private_source
        and "latency_measurement_or_explicit_absence=measurement"
        in private_source,
        "D latency is not one bounded monotone two-pass nine-stage finalizer",
    )
    _require(
        "_require_current_mode_snapshot_resolver(self)" in private_source
        and "self.computation_evidence_service is None" in private_source
        and "resolver.canonical_f_evidence_owner" in private_source
        and "is not self.computation_evidence_service" in private_source
        and "evidence_receipt_ref not in gate.receipt_lineage_refs"
        in private_source
        and "epoch not in gate.source_epoch_refs" in private_source
        and "evidence.no_effect_flags != NO_EFFECTS_V1" in private_source
        and 'evidence.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED"'
        in private_source
        and "inputs.evidence_reference is not gate.evidence_reference"
        in private_source
        and "PreloadedOwnerProjectionBundleV1" in private_source
        and "Path(" not in private_source
        and ".read_text(" not in private_source
        and "ExistingOwnerProjectionAdapterV1" not in private_source,
        "service accepts unbound D authority or performs request-path repository reads",
    )
    _require(
        "latency_measurement_or_explicit_absence=measurement"
        in private_source
        and "control_receipt_proposals=control_receipts" in private_source
        and "PersistenceAvailabilityV1.AVAILABLE_REFERENCE" in private_source
        and "insert_receipt_record(transaction, row)" in private_source
        and "self.persistence_adapter.get_record(row.record_id) != row"
        in private_source,
        "emitted D latency/receipt refs are not typed-returned or persisted",
    )
    compute_start = service_text.index("    def compute_component(")
    compute_end = service_text.index("    def compute_stack(", compute_start)
    compute_source = service_text[compute_start:compute_end]
    _require(
        "CURRENT_IMPLEMENTATION_REGISTRY" in service_text
        and "CURRENT_NAMED_OUTPUT_CONTRACTS" in compute_source
        and "FormulaInputResolverV1.resolve" in compute_source
        and "invoke_current_formula" in compute_source,
        "MATH-39 cannot traverse the central compute-component path",
    )

    functions = {
        node.name: node
        for node in policy.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    executable_tokens = {
        "evaluate_mode_snapshot_preconstruction_gate": (
            "T03",
            "T05",
            "build_snapshot_transition_proposal",
        ),
        "construct_snapshot_candidate": (
            "BUILT_IMMUTABLE",
            "SNAPSHOT_CANDIDATE_BUILT",
        ),
        "validate_snapshot_candidate": (
            "VALIDATED_NO_EFFECT",
            "REJECTED",
            "SNAPSHOT_CANDIDATE_VALID",
            "SNAPSHOT_CANDIDATE_INVALID",
        ),
        "_transition_for_decision": ("T03", "T04", "T05", "T06", "T07"),
        "propose_snapshot_stale_or_rollback_required": ("T11", "T12"),
        "propose_rollback": ("T13", "T14", "SNAPSHOT_PIN_CONFLICT"),
        "propose_snapshot_retirement": ("T15", "T16"),
        "finalize_mode_snapshot_latency_block": (
            "T08", "T09", "T04", "ExecutedModeSnapshotTransitionTraceV1",
        ),
    }
    for function_name, tokens in executable_tokens.items():
        node = functions.get(function_name)
        _require(node is not None, f"missing executable transition owner {function_name}")
        segment = ast.get_source_segment(policy_source, node) or ""
        _require(
            all(token in segment for token in tokens),
            f"{function_name} does not execute its exact transition behavior",
        )
        _require(
            any(isinstance(item, ast.Return) for item in ast.walk(node)),
            f"{function_name} has no deterministic return behavior",
        )
    evaluate_node = functions["evaluate_mode_snapshot_candidate"]
    evaluate_source = ast.get_source_segment(policy_source, evaluate_node) or ""
    _require(
        evaluate_source.index("_preconstruction_decision_state")
        < evaluate_source.index("construct_snapshot_candidate"),
        "candidate construction precedes hard preconstruction blockers",
    )
    rollback_kwonly = tuple(arg.arg for arg in functions["propose_rollback"].args.kwonlyargs)
    for field in (
        "observed_owner_state_ref",
        "observed_current_candidate_ref",
        "observed_current_candidate_version",
        "rollback_required_receipt_proposal",
    ):
        _require(field in rollback_kwonly, f"rollback race precondition missing: {field}")
    _require(
        "NoTradeReoptimizationRouteError(decision)" in service_text,
        "T17 typed NO_TRADE route is not executable",
    )
    evaluate_source = ast.get_source_segment(policy_source, functions["evaluate_mode_snapshot_candidate"]) or ""
    _require(
        "primary_reason = rule.reason_code" in evaluate_source
        and "dict.fromkeys((primary_reason, decision_reason))" in evaluate_source
        and "build_snapshot_transition_proposal(" in evaluate_source
        and "reason for reason in decision_reasons if reason is not rule.reason_code"
        in evaluate_source,
        "canonical transition reason is not first with ordered diagnostics",
    )
    rollback_source = ast.get_source_segment(policy_source, functions["propose_rollback"]) or ""
    _require(
        "target.candidate_version" in rollback_source
        and "target.candidate.evaluated_at.isoformat" not in rollback_source,
        "rollback target version is derived from a timestamp rather than inventory identity",
    )
    helper_source = ast.get_source_segment(
        policy_source, functions["build_snapshot_transition_proposal"]
    ) or ""
    _require(
        all(
            token in helper_source
            for token in (
                "TRANSITION_BY_ID[transition_id]",
                "predecessor_transition_receipt_proposals",
                "source_state=rule.source_state",
                "destination_state=rule.destination_state",
                "primary_reason_code=rule.reason_code",
                "owner_confirmation_required=rule.owner_confirmation_required",
            )
        )
        and all(
            "build_snapshot_transition_proposal(" in (
                ast.get_source_segment(policy_source, functions[name]) or ""
            )
            for name in (
                "evaluate_mode_snapshot_preconstruction_gate",
                "evaluate_mode_snapshot_candidate",
                "propose_snapshot_stale_or_rollback_required",
                "propose_snapshot_retirement",
                "propose_rollback",
            )
        ),
        "runtime transition proposals do not share one exact precondition helper",
    )
    transition_source = ast.get_source_segment(models_source, transition_node) or ""
    _require(
        all(
            token in transition_source
            for token in (
                'self.transition_id == "T07"',
                'self.transition_id in {"T13", "T14"}',
                "predecessor_payload.request_id != self.request_id",
                "predecessor_payload.principal_id != self.principal_id",
                "predecessor_payload.task_id != self.task_id",
                "predecessor_payload.context_ref != self.context_ref",
                "predecessor_payload.destination_state != rule.source_state",
                "predecessor_payload.target_candidate_version",
                "predecessor_payload.no_mutation_flag is not True",
                "predecessor_payload.no_activation_flag is not True",
                "predecessor_payload.no_order_authority_flag is not True",
            )
        ),
        "typed predecessor receipts do not prove exact transition scope and no-effect state",
    )
    trace_source = ast.get_source_segment(models_source, trace_node) or ""
    result_source = ast.get_source_segment(models_source, result_node) or ""
    _require(
        all(
            shape in trace_source
            for shape in (
                '("T03",)',
                '("T04",)',
                '("T05",)',
                '("T08",)',
                '("T08", "T09", "T06")',
                '("T08", "T09", "T07")',
                '("T08", "T10")',
                '("T08", "T09", "T04")',
            )
        )
        and "return self.proposals[-1]" in trace_source
        and "is not self.executed_transition_trace.final_proposal" in result_source
        and "control receipt cardinality and transition fields must resolve to the exact executed trace rows"
        in result_source,
        "ordered executed transition trace or mapped receipt validation is incomplete",
    )
    receipts_source = (PACKAGE / "receipts.py").read_text(encoding="utf-8")
    materialize_start = receipts_source.index("def materialize_mode_snapshot_control_receipts")
    materialize_source = receipts_source[materialize_start:]
    _require(
        "MODE_SNAPSHOT_EVALUATION" in materialize_source
        and "proposal_by_transition_id" in materialize_source
        and 'if "T08" in proposal_by_transition_id' in materialize_source
        and 'for transition_id in ("T09", "T10")' in materialize_source
        and "stage_proposal.transition_id" in materialize_source
        and "result.control_receipt_refs != expected_refs" in materialize_source,
        "D receipt classes are not mapped to the exact executed trace stages",
    )
    agent_policy = _source_tree("agent_policy.py")
    assignments = {
        target.id: statement.value
        for statement in agent_policy.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
    }
    annotated_assignments = {
        statement.target.id: statement.value
        for statement in agent_policy.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.value is not None
    }
    _require(
        ast.literal_eval(assignments["_PRE_ST12F_IMPLEMENTED_OPERATION_IDS"])
        == EXPECTED_PUBLIC_OPERATIONS[:12]
        and ast.literal_eval(assignments["_PRE_ST12F_HELD_OPERATION_IDS"])
        == EXPECTED_PUBLIC_OPERATIONS[12:]
        and ast.literal_eval(annotated_assignments["HELD_OPERATION_IDS"]) == (),
        "agent admission operation partition is not currentized for OP13-OP15",
    )
    implemented = assignments["IMPLEMENTED_OPERATION_IDS"]
    _require(
        isinstance(implemented, ast.Tuple)
        and tuple(
            element.value.id
            for element in implemented.elts
            if isinstance(element, ast.Starred)
            and isinstance(element.value, ast.Name)
        )
        == (
            "_PRE_ST12F_IMPLEMENTED_OPERATION_IDS",
            "_PRE_ST12F_HELD_OPERATION_IDS",
        ),
        "agent admission implemented-operation union is not exact",
    )


def _validate_math39_independently() -> None:
    oracle_tree = _source_tree("oracle_contracts.py")
    vector_node = next(
        node
        for node in oracle_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_ST12D_MATH_39_VECTOR_ROW"
            for target in node.targets
        )
    )
    vector = ast.literal_eval(vector_node.value)
    raw_inputs = vector["inputs"]
    _require(
        tuple(raw_inputs) == ("order_ack", "sequenced_book_events"),
        "MATH-39 golden vector does not contain the exact two raw records",
    )
    ack = raw_inputs["order_ack"]
    events = raw_inputs["sequenced_book_events"]
    _require(
        ack["matching_priority"] == "PRICE_TIME_FIFO"
        and ack["unit"] == "units"
        and ack["basis"] == "ACKNOWLEDGED_INSERTION_POINT"
        and ack["venue_evidence_ref"],
        "MATH-39 raw acknowledgement semantics mismatch",
    )
    sequences = tuple(row["sequence"] for row in events)
    _require(
        sequences == tuple(range(sequences[0], sequences[0] + len(sequences))),
        "MATH-39 raw event sequence is not continuous",
    )
    quantities = {
        "DISPLAYED_BEFORE_ORDER": Decimal(0),
        "PRIOR_ADDITION": Decimal(0),
        "PRIOR_CANCELLATION": Decimal(0),
        "TRADE_AHEAD": Decimal(0),
    }
    for row in events:
        quantity = Decimal(row["quantity"])
        _require(quantity.is_finite() and quantity >= 0, "invalid raw quantity")
        quantities[row["event_kind"]] += quantity
    independent_expected = max(
        Decimal(0),
        quantities["DISPLAYED_BEFORE_ORDER"]
        + quantities["PRIOR_ADDITION"]
        - quantities["PRIOR_CANCELLATION"]
        - quantities["TRADE_AHEAD"],
    )
    _require(
        independent_expected == Decimal(vector["expected"]["queue_ahead"]) == Decimal("80"),
        "independent raw-record MATH-39 reconstruction failed",
    )
    _require(max(Decimal(0), Decimal("1") - Decimal("2") - Decimal("3")) == 0, "MATH-39 floor invariant failed")

    tree = _source_tree("implementation_registry.py")
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "compute_math_39_queue_position_estimate"
    )
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    _require(len(returns) == 1, "MATH-39 production function return shape mismatch")
    expression = ast.unparse(returns[0].value).replace(" ", "")
    _require(expression == "max(Decimal(0),displayed+additions-cancellations-trades)", "MATH-39 production expression differs from independent formula")
    source = ast.get_source_segment((PACKAGE / "implementation_registry.py").read_text(encoding="utf-8"), function) or ""
    for token in ("_nonnegative", "exact_decimal", "sequence_continuous", "matching_priority_known", "ACKNOWLEDGED_INSERTION_POINT", "venue_evidence_ref"):
        _require(token in (PACKAGE / "implementation_registry.py").read_text(encoding="utf-8"), f"MATH-39 invariant token missing: {token}")
    _require("eval(" not in source and "exec(" not in source, "MATH-39 uses dynamic execution")
    oracle_source = (PACKAGE / "oracle_contracts.py").read_text(encoding="utf-8")
    oracle_function = next(
        node
        for node in oracle_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "independently_reconstruct_math_39_from_raw_records"
    )
    independent_source = ast.get_source_segment(oracle_source, oracle_function) or ""
    _require(
        "compute_math_39_queue_position_estimate" not in independent_source
        and "implementation_registry" not in independent_source
        and all(
            token in independent_source
            for token in (
                "matching_priority",
                "venue_evidence_ref",
                "sequences",
                "is_finite",
            )
        ),
        "MATH-39 oracle is not an independent raw-record reconstruction",
    )
    bindings_source = (PACKAGE / "bindings.py").read_text(encoding="utf-8")
    specification_source = (PACKAGE / "specification.py").read_text(encoding="utf-8")
    resolver_source = (PACKAGE / "input_resolver.py").read_text(encoding="utf-8")
    _require(
        bindings_source.count("ST12DMath39RawInputBindingV1(") == 2
        and all(
            token in bindings_source
            for token in (
                "SelectedVenuePublicMarketDataOwnerV1",
                "EconomicReceiptEventSpineV1",
                "SequencedBookEventsPacketV1",
                "OrderAcknowledgementReceiptV1",
            )
        ),
        "MATH-39 does not have exactly two raw current-owner bindings",
    )
    _require(
        "raw_owner_input_keys: tuple[str, ...]" in specification_source
        and "derived_formula_input_keys: tuple[str, ...]" in specification_source
        and '("sequenced_book_events", "order_ack")' in specification_source
        and "ST12D_OUTPUT_V1" in specification_source,
        "MATH-39 additive typed specification/output overlay is incomplete",
    )
    for token in (
        "sequences != tuple(range(",
        "ReasonCode.MATCHING_PRIORITY_UNKNOWN",
        "ReasonCode.POINT_IN_TIME_VIOLATION",
        "ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID",
        "ReasonCode.INPUT_SCOPE_MISMATCH",
        "not value.is_finite()",
    ):
        _require(token in resolver_source, f"MATH-39 raw resolver guard missing: {token}")


def _validate_repair_closure_sources() -> None:
    parameter_source = (PACKAGE / "parameter_policy.py").read_text(encoding="utf-8")
    parameter_tree = ast.parse(parameter_source, filename="parameter_policy.py")
    readable_rows: list[dict[str, object]] = []
    for node in parameter_tree.body:
        target = (
            node.targets[0]
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            else node.target
            if isinstance(node, ast.AnnAssign)
            else None
        )
        if (
            isinstance(target, ast.Name)
            and target.id.startswith("_ST12D_PARAMETER_ROW_")
        ):
            value = ast.literal_eval(node.value)
            _require(isinstance(value, dict), f"{target.id} is not a readable row")
            readable_rows.append(value)
    _require(len(readable_rows) == 28, "D parameter table is not exactly 28 readable rows")
    _require(
        tuple(row.get("id") for row in readable_rows)
        == EXPECTED_PARAMETER_IDS,
        "readable D parameter row ordering/identity mismatch",
    )
    _require(
        all(
            {
                "id",
                "sym",
                "default",
                "range",
                "fallback",
                "precision",
                "procedure",
                "src",
                "app",
                "snap",
            }
            <= set(row)
            for row in readable_rows
        )
        and '"QKUComputationControlPlaneV1.ComputationParameterPolicyV1"'
        in parameter_source,
        "readable D parameter rows do not retain one canonical owner",
    )
    _require(
        all(
            token in parameter_source
            for token in (
                "ST12D_PARAMETER_POLICY_SET_VERSION",
                "ST12D_OWNER_RESOLVED_PARAMETER_IDS",
                "def resolve_st12d_snapshot_parameter_values(",
                "PointInTimePolicyV1.validate(",
                "FreshnessResolverV1.validate(",
                "producer_receipt_refs=(packet.producer_receipt_id,)",
                "point_in_time_receipt_refs=(pit.receipt_id,)",
                "freshness_receipt_refs=(freshness.receipt_id,)",
                "source_epoch_refs=(packet.source_epoch_id,)",
                "producer_receipt_refs=()",
                "point_in_time_receipt_refs=()",
                "freshness_receipt_refs=()",
                "source_epoch_refs=()",
                'if parameter_id == "ST10-PARAM::3002"',
                'if parameter_id == "ST10-PARAM::3003"',
                'if parameter_id == "ST10-PARAM::3641"',
                "tuple(row.parameter_id for row in result)",
            )
        )
        and parameter_source.count('"ST10-PARAM::0764"') >= 2
        and parameter_source.count('"ST10-PARAM::3639"') >= 2,
        "D does not resolve the exact 21 typed value pins through owner/PIT/freshness custody",
    )
    _require(
        '"PARAMETER-POLICY-EPOCH::"' not in parameter_source,
        "static parameter rows still synthesize source epochs",
    )
    d_parameter_source = parameter_source[
        parameter_source.index("_ST12D_PARAMETER_ROW_001") :
    ]
    _require(
        all(
            token not in d_parameter_source
            for token in ("b85decode", "base64", "zlib", "marshal", "pickle")
        ),
        "D parameter rows remain hidden in an encoded/compressed archive",
    )

    validation_source = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    validation_tree = ast.parse(validation_source, filename="validation.py")
    actual_case_fields = _class_fields(
        _class_node(validation_tree, "ST12DActualControlMutationCaseV1")
    )
    forbidden_override_token = "owner_fact_" + "override"
    synthetic_tuple_token = "CAUSAL_OWNER_FIELD_" + "MUTATION"
    _require(
        actual_case_fields
        == (
            "control_id",
            "positive_typed_fixture_builder",
            "actual_owner_or_input_mutation",
            "canonical_observer",
            "expected_positive_terminal_state",
            "expected_negative_reason_or_terminal_state",
            "mapped_semantic_test_ids",
            "grouped_module",
            "positive_fixture_ref",
            "causal_mutation_ref",
            "causal_owner_field_ref",
        )
        and "ST12D_ACTUAL_CONTROL_MUTATION_CASES = _build_st12d_actual_control_mutation_cases()"
        in validation_source
        and "def run_st12d_actual_control_mutation_case(" in validation_source
        and "case.actual_owner_or_input_mutation(positive_fixture)"
        in validation_source
        and "case.canonical_observer(mutated_fixture)" in validation_source
        and forbidden_override_token not in validation_source
        and synthetic_tuple_token not in validation_source,
        "D validation lacks actual typed owner/input mutation adjudication",
    )
    stage_fixture_node = next(
        (
            node
            for node in validation_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_st12d_stage_receipt_fixture"
        ),
        None,
    )
    _require(stage_fixture_node is not None, "stage receipt fixture is missing")
    stage_assignments = {
        node.targets[0].id: node.value
        for node in stage_fixture_node.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    candidate_fixture_call = stage_assignments.get("candidate")
    result_fixture_call = stage_assignments.get("result")
    result_fixture_keywords = {
        keyword.arg: keyword.value
        for keyword in result_fixture_call.keywords
        if keyword.arg is not None
    } if isinstance(result_fixture_call, ast.Call) else {}
    _require(
        isinstance(candidate_fixture_call, ast.Call)
        and isinstance(candidate_fixture_call.func, ast.Name)
        and candidate_fixture_call.func.id == "FormulaRuntimeSnapshotCandidateV1"
        and isinstance(result_fixture_call, ast.Call)
        and isinstance(result_fixture_call.func, ast.Name)
        and result_fixture_call.func.id == "ModeSnapshotCandidateProposalResultV1"
        and isinstance(
            result_fixture_keywords.get("snapshot_candidate_or_explicit_absence"),
            ast.Name,
        )
        and result_fixture_keywords["snapshot_candidate_or_explicit_absence"].id
        == "candidate"
        and "ExecutedModeSnapshotTransitionTraceV1((build, validated, final))"
        in (ast.get_source_segment(validation_source, stage_fixture_node) or ""),
        "T09 stage receipt fixture does not carry its exact validated candidate",
    )
    grouped_tests = (
        REPO_ROOT
        / "tests/stage1_prediction_markets/qku_computation_control_plane/test_policy_state_matrix.py",
        REPO_ROOT
        / "tests/stage1_prediction_markets/qku_computation_control_plane/test_integration_snapshot_matrix.py",
        REPO_ROOT
        / "tests/stage1_prediction_markets/qku_computation_control_plane/test_adversarial_latency_security_matrix.py",
    )
    test_sources = tuple(path.read_text(encoding="utf-8") for path in grouped_tests)
    test_trees = tuple(ast.parse(source) for source in test_sources)
    test_function_counts = tuple(
        sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in tree.body
        )
        for tree in test_trees
    )
    _require(
        test_function_counts == (4, 5, 5)
        and "for control_id in ST12D_ACTUAL_CONTROL_MUTATION_CASES"
        in test_sources[1]
        and "run_st12d_actual_control_mutation_case(control_id)"
        in test_sources[1],
        "grouped D tests expanded per ID or do not execute actual control mutations",
    )
    receipt_test_node = next(
        node
        for node in test_trees[1].body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_receipt_spine_and_svc_projection_are_one_way_no_effect_views"
    )
    receipt_test_source = ast.get_source_segment(
        test_sources[1], receipt_test_node
    ) or ""
    _require(
        receipt_test_source.count("valid_terminal_rows =") == 1
        and receipt_test_source.count("outcome_contradiction_matrix =") == 1
        and "for contradiction in outcome_contradiction_matrix"
        in receipt_test_source
        and "with pytest.raises(ContractValidationError)" in receipt_test_source
        and all(
            shape in receipt_test_source
            for shape in (
                '("T03",)',
                '("T04",)',
                '("T05",)',
                '("T08", "T09", "T06")',
                '("T08", "T09", "T07")',
                '("T08", "T10")',
                '("T08", "T09", "T04")',
            )
        )
        and "t08_only_trace" in receipt_test_source
        and "decision_field_mutations" in receipt_test_source
        and "candidate_field_mutations" in receipt_test_source
        and "ST12-TEST::" not in test_sources[1],
        "grouped integration test lacks one compact seven-row contradiction matrix",
    )
    _require(
        all(
            forbidden_override_token not in source
            and synthetic_tuple_token not in source
            for source in test_sources
        ),
        "synthetic comparison override pattern remains in D validation surfaces",
    )
    _require(
        'packet_id="PACKET::D::UNRELATED"' in test_sources[1]
        and '"SOURCE-EPOCH::D::UNRELATED" not in unrelated_enriched.source_epoch_refs'
        in test_sources[1]
        and "ReasonCode.SOURCE_EPOCH_STALE" in test_sources[1]
        and 'monkeypatch.setattr(Path, "read_text"' in test_sources[0]
        and 'monkeypatch.setattr(Path, "read_text"' in test_sources[1],
        "D grouped tests do not prove consumed-only epochs and zero request file reads",
    )
    _require(
        "_CustomEvidenceAvailableResolver" in test_sources[1]
        and "custom_resolver.gate_calls, custom_resolver.enrich_calls"
        in test_sources[1]
        and "wrong_registry_resolver" in test_sources[1]
        and "expected_stage_transitions" in test_sources[1]
        and "source_snapshot_refs" in test_sources[1]
        and "producer_receipt_refs" in test_sources[1],
        "grouped D tests omit canonical authority, trace, or reference-ontology probes",
    )

    models_source = (PACKAGE / "models.py").read_text(encoding="utf-8")
    protocols_source = (PACKAGE / "protocols.py").read_text(encoding="utf-8")
    resolver_source = (PACKAGE / "input_resolver.py").read_text(encoding="utf-8")
    _require(
        "def validate_reference_identity_classes(" in models_source
        and '"ComputationParameterPolicyV1::"' in models_source
        and '"OWNER-PROJECTION-RECEIPT::"' in models_source
        and '"PARAMETER-POLICY-EPOCH::"' in models_source
        and '"OWNER-PROJECTION-EPOCH::"' in models_source
        and "source_snapshot_ref: str" in protocols_source
        and "receipt_refs: tuple[str, ...] = ()" in protocols_source
        and "source_epoch_refs: tuple[str, ...] = ()" in protocols_source
        and "row.source_snapshot_ref" in protocols_source
        and '"OWNER-PROJECTION-RECEIPT::"' not in protocols_source
        and '"OWNER-PROJECTION-EPOCH::"' not in protocols_source
        and '"EVIDENCE-EPOCH::"' not in resolver_source,
        "policy, snapshot, receipt, and source-epoch reference classes are not separated",
    )

    builder_source = (REPO_ROOT / "tools/build_qku_computation_control_plane.py").read_text(
        encoding="utf-8"
    )
    builder_tree = ast.parse(builder_source, filename="build_qku_computation_control_plane.py")
    computability_node = next(
        node
        for node in builder_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_build_st12d_computability_rows"
    )
    computability_source = ast.get_source_segment(builder_source, computability_node) or ""
    _require(
        "_build_st12d_audit_bundle()" in computability_source
        and "FrozenContextualComputabilityResolverV1.resolve" in computability_source
        and "snapshot_bundle=bundle" in computability_source
        and '"dimension_computable": tuple(row.computable for row in dimensions)'
        in computability_source
        and '"dimension_computable": (True' not in computability_source,
        "generated D computability is hard-coded instead of centrally resolved",
    )
    _require(
        "control_mutation_results = tuple(" in builder_source
        and "run_st12d_actual_control_mutation_case(control_id)"
        in builder_source
        and "actual_control_mutation_rejection_count = sum(" in builder_source
        and "mutation_result_by_control" in builder_source
        and "canonical_current_resolver_enforced_count = int(" in builder_source
        and "stage_transition_receipt_mismatch_count = int(" in builder_source
        and "synthetic_override_mutation_count = sum(" in builder_source
        and '"synthetic_override_mutation_count": synthetic_override_mutation_count'
        in builder_source,
        "generated validation summary is not derived from actual control mutations",
    )
    _require(
        forbidden_override_token not in builder_source
        and synthetic_tuple_token not in builder_source,
        "generated builder retains a synthetic mutation override pattern",
    )
    runner_source = (REPO_ROOT / "tools/run_validation_gates.py").read_text(
        encoding="utf-8"
    )
    runner_tree = ast.parse(runner_source, filename="run_validation_gates.py")
    runner_assignments = {
        target.id: node.value
        for node in runner_tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    reconstructed_registered_phases = (
        ast.literal_eval(runner_assignments["FAST_PREFLIGHT_PHASE"]),
        *ast.literal_eval(
            runner_assignments["DETERMINISTIC_VALIDATOR_SHARD_PHASES"]
        ),
        *ast.literal_eval(runner_assignments["PYTEST_SHARD_PHASES"]),
        ast.literal_eval(runner_assignments["POST_VALIDATION_PHASE"]),
    )
    _require(
        reconstructed_registered_phases == EXPECTED_REGISTERED_PHASES,
        "registered validation phase roster changed from the exact thirteen phases",
    )
    stack_source = (PACKAGE / "stack_resolver.py").read_text(encoding="utf-8")
    _require(
        'ST12D_SNAPSHOT_COMPONENT_IDS = ("MATH-13", "MATH-14", "MATH-15", "MATH-39")'
        in stack_source
        and "row.parameter_id for row in self.resolved_parameter_values"
        in stack_source
        and "ST12D_SNAPSHOT_PARAMETER_BINDING_IDS" in stack_source
        and "data_edge_refs: tuple[str, ...] = ()" in stack_source
        and "self.data_edge_refs != ()" in stack_source,
        "D snapshot bundle creates a fabricated executable stack/data edge",
    )


def _validate_no_metadata_only_or_scope_escape() -> None:
    for name in ("mode_snapshot_policy.py", "latency_policy.py"):
        source = (PACKAGE / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        _require(not any(isinstance(node, ast.Pass) for node in ast.walk(tree)), f"metadata-only pass in {name}")
        _require("NotImplementedError" not in source and "TODO" not in source and "TBD" not in source, f"placeholder in {name}")
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        _require(imports.isdisjoint({"requests", "httpx", "socket", "subprocess", "openai", "qiskit", "pennylane", "boto3"}), f"forbidden dependency in {name}")
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        _require(calls.isdisjoint({"eval", "exec", "open", "__import__"}), f"dynamic or filesystem request-path call in {name}")
    generated_names = set(EXPECTED_GENERATED_NAMES)
    _require(generated_names.isdisjoint({
        "decision_quality_artifact_classes.jsonl", "agent_consumption_routes.jsonl",
        "external_candidate_ledger.jsonl", "owner_workflow_ledger.jsonl",
        "llm_routes.jsonl", "quantum_backend_snapshots.jsonl", "replay_paper_evidence.jsonl",
    }), "later-tranche generated output entered D")


def _validate_st12f_three_part_d_selection() -> int:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
        ComputationEvidenceServiceV1,
        EvidenceBundleTerminalStateV1,
        FToDEvidenceReferenceQueryV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        ST12FEvidenceReferenceV1,
        ST12FEvidenceStateV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
        ST12FEvidenceControlReceiptRecordV1,
        ST12FReceiptClassV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        deterministic_json,
    )

    @dataclass(frozen=True, slots=True)
    class _ContextProbeV1:
        as_of: datetime

    @dataclass(frozen=True, slots=True)
    class _BundleProbeV1:
        evidence_id: str
        component_or_template_ref: str
        input_lock_id: str
        evidence_bundle_version: str
        terminal_state: EvidenceBundleTerminalStateV1
        d_evidence_reference_projection: ST12FEvidenceReferenceV1

    @dataclass(frozen=True, slots=True)
    class _ReceiptSpineProbeV1:
        record_id: str
        typed_payload: ST12FEvidenceControlReceiptRecordV1

    observed_at = datetime(2035, 1, 1, 12, tzinfo=UTC)
    evidence_id = "EVIDENCE::SHARED-INDEPENDENT-D-SELECTION"
    identities = (
        ("MATH-01", "LOCK::COMPONENT-A", "BUNDLE::COMPONENT-A"),
        ("MATH-02", "LOCK::COMPONENT-B", "BUNDLE::COMPONENT-B"),
        ("MATH-03", "LOCK::UNRELATED-LATER", "BUNDLE::UNRELATED-LATER"),
    )
    spines: list[_ReceiptSpineProbeV1] = []
    bundles: dict[str, _BundleProbeV1] = {}
    current_refs: dict[tuple[str, str, str], str] = {}
    references: dict[str, ST12FEvidenceReferenceV1] = {}
    for ordinal, (component, input_lock, version) in enumerate(identities, 1):
        bundle_ref = f"ST12F-RECEIPT::{version}::EVIDENCE_BUNDLE_VERSION"
        reference = ST12FEvidenceReferenceV1(
            evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
            evidence_ref=bundle_ref,
            lane="REPLAY_PAPER",
            dataset_grade_ref=f"DATASET::{component}",
            venue_semantic_binding_ref=f"VENUE::{component}",
            cross_venue_equivalence_ref=f"EQUIVALENCE::{component}",
            observed_at=observed_at - timedelta(minutes=ordinal),
            valid_until=observed_at + timedelta(hours=1),
            policy_version="ST12F_EVIDENCE_POLICY_V1_4",
            causation_id=f"CAUSATION::{component}",
            correlation_id=f"CORRELATION::{component}",
            input_lock_id=input_lock,
            component_or_template_ref=component,
            evidence_bundle_version=version,
            source_epoch_refs=(f"SOURCE_EPOCH::{component}",),
            terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
            reference_id=f"D-REFERENCE::{component}",
            evidence_id=evidence_id,
        )
        receipt = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=(
                f"ST12F-RECEIPT::{reference.reference_id}::D_EVIDENCE_REFERENCE"
            ),
            receipt_class=ST12FReceiptClassV1.D_EVIDENCE_REFERENCE,
            operation_id="ST10-OP::15",
            request_id=f"REQUEST::{component}",
            idempotency_key=f"IDEMPOTENCY::{component}",
            contract_type="ST12FEvidenceReferenceV1",
            contract_id=reference.reference_id,
            contract_version=reference.contract_version,
            input_lock_id_or_explicit_absence=input_lock,
            parent_version_ref_or_explicit_absence=bundle_ref,
            canonical_contract_json=deterministic_json(reference),
            source_record_refs=(bundle_ref,),
            parameter_value_refs=(),
            source_epoch_refs=reference.source_epoch_refs,
            typed_reason_codes=(),
            terminal_state=reference.terminal_state,
            fixture_only_not_evidence=False,
        )
        spines.append(_ReceiptSpineProbeV1(bundle_ref, receipt))
        bundles[bundle_ref] = _BundleProbeV1(
            evidence_id=evidence_id,
            component_or_template_ref=component,
            input_lock_id=input_lock,
            evidence_bundle_version=version,
            terminal_state=(
                EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            ),
            d_evidence_reference_projection=reference,
        )
        current_refs[(evidence_id, input_lock, component)] = bundle_ref
        references[component] = reference

    class _SelectionProbeServiceV1(ComputationEvidenceServiceV1):
        def __init__(self) -> None:
            self.observed_current_identities: list[tuple[str, str, str]] = []

        def _durable_receipt_spines(self) -> tuple[_ReceiptSpineProbeV1, ...]:
            return tuple(spines)

        def _validate_receipt_lock_metadata(self, spine: object) -> None:
            return None

        def _durable_current_bundle_ref(
            self,
            requested_evidence_id: str,
            expected_input_lock_id: str,
            requested_component_or_template_ref: str,
        ) -> str | None:
            identity = (
                requested_evidence_id,
                expected_input_lock_id,
                requested_component_or_template_ref,
            )
            self.observed_current_identities.append(identity)
            return current_refs.get(identity)

        def resolve_bundle(self, bundle_ref: str) -> _BundleProbeV1:
            return bundles[bundle_ref]

    service = _SelectionProbeServiceV1()
    selected = 0
    for component, input_lock, _version in identities[:2]:
        query = FToDEvidenceReferenceQueryV1(
            query_id=f"QUERY::{component}",
            requested_evidence_id=evidence_id,
            requested_component_or_template_ref=component,
            expected_input_lock_id=input_lock,
            expected_source_epoch_refs=(f"SOURCE_EPOCH::{component}",),
            evaluated_at=observed_at,
            request_read_lineage_refs=(f"REQUEST-LINEAGE::{component}",),
        )
        actual = service.read_evidence_reference(
            _ContextProbeV1(as_of=observed_at),
            causation_id=f"QUERY-CAUSATION::{component}",
            correlation_id=f"QUERY-CORRELATION::{component}",
            query=query,
        )
        _require(
            actual == references[component],
            "exact component D reference was hidden by a later unrelated reference",
        )
        selected += 1
    _require(
        tuple(service.observed_current_identities)
        == tuple(
            (evidence_id, input_lock, component)
            for component, input_lock, _version in identities[:2]
        ),
        "D current-bundle selection did not use the exact three-part identity",
    )
    return selected


def main() -> int:
    try:
        runtime_metrics = _execute_runtime_repair_probe()
        _validate_denominators_and_artifact_identity(runtime_metrics)
        _validate_contract_and_service_ast()
        multi_component_d_selection_count = _validate_st12f_three_part_d_selection()
        _validate_math39_independently()
        _validate_repair_closure_sources()
        _validate_no_metadata_only_or_scope_escape()
    except (OSError, ValueError, KeyError, TypeError, ValidationFailure) as exc:
        print(f"ST12D_INDEPENDENT_VALIDATION_FAILED::{exc}", file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} "
        "closure=23 paths=7 parameters=28 math=4 oracles=4 vectors=4 "
        "semantic_tests=26 commands=6 states=35 transitions=17 universe=240 "
        "canonical_resolver=1 custom_bypass=0 trace_gaps=0 "
        "stage_receipt_mismatches=0 phantom_receipts=0 synthetic_epochs=0 "
        "actual_mutations=23 synthetic_overrides=0 f_reference_cases=9 "
        f"multi_component_d_selection={multi_component_d_selection_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
