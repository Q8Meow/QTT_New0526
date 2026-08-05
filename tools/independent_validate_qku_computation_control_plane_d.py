#!/usr/bin/env python3
"""Independent source-and-artifact validator for the exact ST12-D boundary.

This validator deliberately does not import QKU production modules or use a
production callable as an oracle.  Frozen expectations are reconstructed here,
then compared with source AST and builder-owned reference-only projections.
"""

from __future__ import annotations

import ast
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
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
EXPECTED_COMMANDS = (
    "python tools/independent_validate_qku_computation_control_plane_execution.py",
    "python tools/independent_validate_qku_computation_control_plane_latency.py",
    "python tools/independent_validate_qku_computation_control_plane_security.py",
    "python tools/validate_qku_computation_control_plane.py --domain execution",
    "python tools/validate_qku_computation_control_plane.py --domain latency",
    "python tools/validate_qku_computation_control_plane.py --domain security",
)
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
        "proposal_id", "source_candidate_ref_or_explicit_absence", "target_candidate_ref",
        "source_candidate_version_or_explicit_absence", "target_candidate_version",
        "transition_id", "expected_owner_state_ref", "precondition_receipt_refs",
        "proposed_state", "typed_reason_codes", "causation_id", "correlation_id",
        "active_pointer_commit_allowed", "mutation_allowed",
        "runtime_effect_authorized", "order_release_authorized",
    ),
    "ModeSnapshotCandidateProposalResultV1": (
        "snapshot_candidate_or_explicit_absence", "mode_snapshot_decision",
        "snapshot_transition_proposal", "control_receipt_refs",
        "owner_projection_or_explicit_absence", "no_authority_flag",
    ),
    "ModeSnapshotControlReceiptRecordV1": (
        "control_receipt_id", "control_class", "request_id", "task_id", "principal_id",
        "capability_decision_ref", "context_ref",
        "snapshot_candidate_ref_or_explicit_absence", "mode_snapshot_decision_ref",
        "transition_proposal_ref", "implementation_pin_refs", "parameter_value_refs",
        "source_epoch_refs", "state_before_refs", "state_after_refs",
        "typed_reason_codes", "fallback_route", "owner_review_route",
        "latency_measurement_ref_or_explicit_absence", "owner_action_policy_ref",
        "no_order_authority_flag",
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


def _validate_denominators_and_artifact_identity() -> tuple[
    dict[str, object], tuple[dict[str, object], ...], tuple[dict[str, object], ...]
]:
    _require(ARTIFACTS.is_dir(), "ST12-D generated owner directory is missing")
    names = tuple(sorted(path.name for path in ARTIFACTS.iterdir() if path.is_file()))
    _require(names == tuple(sorted(EXPECTED_GENERATED_NAMES)), "generated path set is not exact")
    manifest = _read_json(ARTIFACTS / "manifest.json")
    summary = _read_json(ARTIFACTS / "validation_summary.json")
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
    semantic_predicate_refs = tuple(row["exact_fields_or_refs"][1] for row in semantic_rows)
    semantic_mutation_refs = tuple(
        row.get("mutation_test_ref_or_explicit_not_material")
        for row in semantic_rows
    )
    _require(
        len(set(semantic_predicate_refs)) == 26
        and len(set(semantic_mutation_refs)) == 26
        and not (set(control_predicate_refs) & set(semantic_predicate_refs)),
        "26 semantic identities lack unique executable predicates and mutations",
    )
    _require(tuple(row["exact_fields_or_refs"][0] for row in universe if row.get("input_class") == "certified_command") == EXPECTED_COMMANDS, "six certified commands mismatch")
    _require(tuple(row.get("member_ref", "").rsplit("::", 1)[-1] for row in universe if row.get("input_class") == "math_component") == EXPECTED_MATH_IDS, "four math identities mismatch")
    _require(sum(row.get("input_class") == "independent_oracle" for row in universe) == 4, "four independent oracles missing")
    _require(sum(row.get("input_class") == "golden_vector" for row in universe) == 4, "four golden vectors missing")
    _require(
        manifest.get("row_specific_predicate_count") == 49
        and manifest.get("predicate_positive_pass_count") == 49
        and manifest.get("predicate_causal_mutation_rejection_count") == 49
        and summary.get("row_specific_predicate_count") == 49
        and summary.get("predicate_positive_pass_count") == 49
        and summary.get("predicate_causal_mutation_rejection_count") == 49,
        "49 row-specific predicates are not positive and mutation-sensitive",
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
    models = _source_tree("models.py")
    receipts = _source_tree("receipts.py")
    for class_name, expected_fields in EXPECTED_CONTRACT_FIELDS.items():
        tree = receipts if class_name == "ModeSnapshotControlReceiptRecordV1" else models
        _require(_class_fields(_class_node(tree, class_name)) == expected_fields, f"{class_name} field roster mismatch")

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
    _require(
        "pre_f_unavailable_reference(" in input_resolver_source
        and "preflight_snapshot_computation_bundle(" in input_resolver_source
        and "ExistingOwnerProjectionAdapterV1(self._repo_root)" in input_resolver_source,
        "current D resolver does not derive evidence, bundle, and owner views",
    )

    decision_fields = _class_fields(_class_node(models, "ModeSnapshotDecisionV1"))
    _require(decision_fields[-3:] == ("runtime_effect_authorized", "active_pointer_commit_allowed", "order_release_authorized"), "decision effect boundary mismatch")
    candidate_node = _class_node(models, "FormulaRuntimeSnapshotCandidateV1")
    transition_node = _class_node(models, "SnapshotTransitionProposalV1")
    receipt_node = _class_node(receipts, "ModeSnapshotControlReceiptRecordV1")
    for node, names, expected in (
        (candidate_node, ("runtime_effect_authorized", "order_release_authorized", "activated"), False),
        (transition_node, ("active_pointer_commit_allowed", "mutation_allowed", "runtime_effect_authorized", "order_release_authorized"), False),
        (receipt_node, ("no_order_authority_flag",), True),
    ):
        defaults = {
            item.target.id: item.value
            for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        }
        for name in names:
            _require(isinstance(defaults.get(name), ast.Constant) and defaults[name].value is expected, f"{node.name}.{name} default mismatch")

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
    admission_offset = service_text.index("capability_decision = _admit_agent_request", service_text.index("def submit_candidate_proposal"))
    discriminator_offset = service_text.index("request.candidate_kind", admission_offset)
    _require(admission_offset < discriminator_offset, "candidate kind is read before central admission")
    private_offset = service_text.index("def _submit_mode_snapshot_candidate")
    safety_offset = service_text.index("validate_current_kill_submit_state", private_offset)
    evidence_offset = service_text.index("expected_evidence = pre_f_unavailable_reference", private_offset)
    schema_offset = service_text.index("_validate_d_proposed_specification(request, inputs)", private_offset)
    body_source_offset = service_text.index("source_candidate_refs = request.source_candidate_refs", private_offset)
    _require(
        safety_offset < evidence_offset < schema_offset < body_source_offset,
        "kill/submit and truthful pre-F evidence are not enforced before D schema/body reads",
    )
    latency_offset = service_text.index("latency_decision = evaluate_latency_profile", private_offset)
    projection_offset = service_text.index("final_projection = projection_adapter.project_mode_snapshot", private_offset)
    projection_attach_offset = service_text.index("owner_projection_or_explicit_absence=final_projection", private_offset)
    receipts_offset = service_text.index("materialize_mode_snapshot_control_receipts", private_offset)
    _require(
        latency_offset < projection_offset < projection_attach_offset < receipts_offset,
        "final owner projection or receipts precede the final post-latency decision",
    )
    private_source = service_text[private_offset:service_text.index("def _", private_offset + 5)]
    _require(
        "type(resolver) is not CurrentModeSnapshotInputResolverV1" in private_source
        and "resolver.owner_registry is not self.owner_registry" in private_source
        and "inputs.evidence_reference != expected_evidence" in private_source,
        "service accepts injected D resolver/evidence authority",
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
        < evaluate_source.index("build_snapshot_candidate"),
        "candidate construction precedes hard preconstruction blockers",
    )
    rollback_kwonly = tuple(arg.arg for arg in functions["propose_rollback"].args.kwonlyargs)
    for field in (
        "observed_owner_state_ref",
        "observed_current_candidate_ref",
        "observed_current_candidate_version",
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
        and "typed_reason_codes=decision_reasons" in evaluate_source,
        "canonical transition reason is not first with ordered diagnostics",
    )
    rollback_source = ast.get_source_segment(policy_source, functions["propose_rollback"]) or ""
    _require(
        "target.candidate_version" in rollback_source
        and "target.candidate.evaluated_at.isoformat" not in rollback_source,
        "rollback target version is derived from a timestamp rather than inventory identity",
    )
    receipts_source = (PACKAGE / "receipts.py").read_text(encoding="utf-8")
    materialize_start = receipts_source.index("def materialize_mode_snapshot_control_receipts")
    materialize_source = receipts_source[materialize_start:]
    _require(
        "MODE_SNAPSHOT_EVALUATION" in materialize_source
        and "snapshot_candidate_state is not SnapshotCandidateStateV1.ABSENT" in materialize_source
        and "SnapshotCandidateStateV1.REJECTED" in materialize_source
        and "len(result.control_receipt_refs) != len(control_class_tuple)" in materialize_source,
        "D receipt classes are not derived from actually executed stages",
    )
    _require(_git_path_changed("src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py") is False, "agent_policy.py edit count is nonzero")


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
    _require(
        "class ST12DPredicateSpecV1" in validation_source
        and "ST12D_PREDICATE_SPECS = _build_st12d_predicate_specs()"
        in validation_source
        and "def adjudicate_st12d_predicate(" in validation_source
        and "owner_fact_override" in validation_source
        and "actual == spec.expected_owner_fact" in validation_source
        and "_st12d_predicate_matrix" not in validation_source,
        "D validation still uses broad shared booleans or lacks causal adjudication",
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
    test_function_count = sum(
        sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.parse(source).body
        )
        for source in test_sources
    )
    _require(
        test_function_count < 23
        and "for semantic_id, predicate in ST12D_PREDICATE_SPECS.items()"
        in test_sources[1]
        and "owner_fact_override=predicate.causal_mutation_fact"
        in test_sources[1],
        "grouped D tests expanded per ID or do not execute causal mutations",
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
        "predicate_positive_pass_count = sum(" in builder_source
        and "predicate_causal_mutation_rejection_count = sum(" in builder_source
        and "adjudicate_st12d_predicate(" in builder_source,
        "generated validation summary is not derived from actual predicate adjudication",
    )
    stack_source = (PACKAGE / "stack_resolver.py").read_text(encoding="utf-8")
    _require(
        'ST12D_SNAPSHOT_COMPONENT_IDS = ("MATH-13", "MATH-14", "MATH-15", "MATH-39")'
        in stack_source
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


def main() -> int:
    try:
        _validate_denominators_and_artifact_identity()
        _validate_contract_and_service_ast()
        _validate_math39_independently()
        _validate_repair_closure_sources()
        _validate_no_metadata_only_or_scope_escape()
    except (OSError, ValueError, KeyError, TypeError, ValidationFailure) as exc:
        print(f"ST12D_INDEPENDENT_VALIDATION_FAILED::{exc}", file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} "
        "closure=23 paths=7 parameters=28 math=4 oracles=4 vectors=4 "
        "semantic_tests=26 commands=6 states=35 transitions=17 universe=240"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
