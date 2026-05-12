#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas") / "edge" / "edge_parameter_stack_selection_packet.schema.json"
)
DEFAULT_PRODUCTION_PACKET = (
    pathlib.Path("docs") / "master_plan" / "edge" / "EDGEParameterStackSelectionPacket.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "edge"
    / "synthetic_edge_parameter_stack_selection_packet.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "EDGEParameterStackSelectionPacket.report.json"
)

PR73_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_role_taxonomy.schema.json"
)
PR73_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackRoleTaxonomy.yaml"
)
PR73_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackRoleTaxonomy.report.json"
)
PR73_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"
PR74_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_completeness_gate.schema.json"
)
PR74_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompletenessGate.yaml"
)
PR74_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompletenessGate.report.json"
)
PR74_VALIDATOR = (
    pathlib.Path("tools") / "validate_atomicrows_parameter_stack_completeness_gate.py"
)
PR75_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_compatibility_gate.schema.json"
)
PR75_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompatibilityGate.yaml"
)
PR75_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompatibilityGate.report.json"
)
PR75_VALIDATOR = (
    pathlib.Path("tools") / "validate_atomicrows_parameter_stack_compatibility_gate.py"
)

CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
PR76_SHORT_TEST = (
    pathlib.Path("tests")
    / "source_evidence"
    / "test_runtime_resolver_allowlist_live_blocks.py"
)
PR76_OLD_LONG_TEST = (
    pathlib.Path("tests")
    / "source_evidence"
    / "test_stage1_runtime_resolver_snapshot_consumer_allowlist_blocks_direct_live_dual_review_dashboard.py"
)

PACKET_ID = "EDGE_PARAMETER_STACK_SELECTION_PACKET"
PACKET_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-EDGE-PACKET-SCHEMA"
REPORT_ID = "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_edge_parameter_stack_selection_packet.py"
AUTHORITY_CLASS = (
    "STATIC_EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_ONLY_NOT_STACK_SELECTION_"
    "NOT_SCORING_NOT_ROUTING_NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_STACK_SELECTION_NOT_SCORING_NOT_ROUTING_NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"
FAILURE_MARKER = "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_FAILED"

PR73_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
PR74_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
PR75_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"

REQUIRED_STACK_ROLES = (
    "SIGNAL",
    "SCORING",
    "NORMALIZATION",
    "RISK",
    "EXECUTION",
    "CAPITAL",
    "LATENCY",
    "ERROR_GUARD",
    "QUANTUM_ADVISORY",
)
ROLE_FAMILY_FIELD_BY_ROLE = {
    "SIGNAL": "selected_signal_family_ids",
    "SCORING": "selected_scoring_family_ids",
    "NORMALIZATION": "selected_normalization_family_ids",
    "RISK": "selected_risk_family_ids",
    "EXECUTION": "selected_execution_family_ids",
    "CAPITAL": "selected_capital_family_ids",
    "LATENCY": "selected_latency_family_ids",
    "ERROR_GUARD": "selected_error_guard_family_ids",
    "QUANTUM_ADVISORY": "selected_quantum_advisory_family_ids",
}
SELECTED_FAMILY_FIELDS = tuple(ROLE_FAMILY_FIELD_BY_ROLE.values())

ROLE_COMPLETION_STATES = (
    "ROLE_COMPLETE",
    "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE",
    "ROLE_INCOMPLETE_DUPLICATE_ROLE",
    "ROLE_INCOMPLETE_SINGLE_PARAMETER_ONLY",
    "ROLE_INCOMPLETE_SINGLE_ALGORITHM_ONLY",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_STACK_READINESS_ONLY",
    "SYNTHETIC_FIXTURE_ONLY_NOT_PRODUCTION_READY",
)
COMPATIBILITY_STATES = (
    "COMPATIBILITY_COMPLETE",
    "COMPATIBILITY_BLOCKED_UPSTREAM_ROLE_INCOMPLETE",
    "COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE",
    "COMPATIBILITY_INCOMPLETE_INTERFACE_MISMATCH",
    "COMPATIBILITY_INCOMPLETE_DUPLICATE_INTERFACE",
    "COMPATIBILITY_INCOMPATIBLE_AUTHORITY_TRANSITION",
    "COMPATIBILITY_INCOMPATIBLE_SOURCE_FACT_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_CONNECTOR_SEMANTIC_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_COMPATIBILITY_ONLY",
    "SYNTHETIC_FIXTURE_ONLY_NOT_PRODUCTION_READY",
)
SOURCE_DEPENDENCY_STATES = (
    "SOURCE_DEPENDENCY_STATIC_DECLARED_NOT_ACCEPTED",
    "SOURCE_DEPENDENCY_ACCEPTED_PACKET_REQUIRED_BEFORE_CONNECTOR_OR_LIVE_USE",
    "SOURCE_DEPENDENCY_OWNER_POLICY_SCOPE_ONLY_NOT_EXTERNAL_FACT",
    "SOURCE_DEPENDENCY_BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET",
    "SYNTHETIC_FIXTURE_ONLY_NOT_SOURCE_AUTHORITY",
)
ALLOWED_BUNDLE_DIGEST_REFS = (
    "ATOMICROWS_BUNDLE_DIGEST_DEFERRED_UNTIL_APPROVED_BUNDLE_PR",
    "ATOMICROWS_BUNDLE_DIGEST_NOT_CREATED_STATIC_SCHEMA_ONLY",
)

MINIMUM_REQUIRED_PACKET_FIELDS = (
    "edge_id",
    "edge_hypothesis_packet_id",
    "atomicrows_bundle_digest_ref",
    "selected_stack_id",
    "venue_scope",
    "edge_type",
    "strategy_class",
    "market_type",
    "latency_sensitivity_class",
    "capital_intensity_class",
    "source_dependency_state",
    "selected_signal_family_ids",
    "selected_scoring_family_ids",
    "selected_normalization_family_ids",
    "selected_risk_family_ids",
    "selected_execution_family_ids",
    "selected_capital_family_ids",
    "selected_latency_family_ids",
    "selected_error_guard_family_ids",
    "selected_quantum_advisory_family_ids",
    "blocked_row_ids_and_reasons",
    "role_completion_state",
    "compatibility_state",
    "candidate_stack_generation_count",
    "replay_paper_competition_required_flag",
    "owner_review_required_flag",
)
SCHEMA_REQUIRED_FIELDS = (
    "packet_id",
    "packet_version",
    "semantic_task_id",
    "authority_class",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "depends_on_parameter_stack_compatibility_gate",
    "required_stack_role_family_fields",
    "minimum_required_packet_fields",
    "static_packet_policy",
    *MINIMUM_REQUIRED_PACKET_FIELDS,
    "owner_override_policy",
    "quantum_advisory_policy",
    "source_evidence_boundary_policy",
    "atomicrows_bundle_boundary_policy",
    "future_consumer_contract",
    "explicit_no_claim_flags",
    "validation_invariants",
    "production_readiness",
    "final_ready",
)

OWNER_OVERRIDE_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
)
QUANTUM_TRUE_FIELDS = (
    "selected_quantum_advisory_family_ids_required",
    "quantum_advisory_static_metadata_only",
    "future_quantum_applicability_registry_required_before_quantum_selection",
    "future_owner_quantum_priority_policy_required_before_quantum_priority_selection",
    "future_optimizer_arbitration_gate_required_before_optimizer_choice",
    "strongest_classical_comparator_required_before_quantum_advantage_claim",
    "fallback_bundle_required_before_quantum_runtime_use",
    "replay_paper_evidence_required_before_advantage_claim",
    "live_evidence_required_before_profit_claim",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_scoring_created",
    "quantum_ranking_created",
    "quantum_selection_created",
    "quantum_arbitration_created",
)
SOURCE_TRUE_FIELDS = (
    "owner_policy_may_authorize_retrieval_scope",
    "external_fact_requires_accepted_source_packet",
    "connector_semantic_requires_accepted_source_packet",
    "source_dependency_state_is_static_metadata_only",
)
SOURCE_FALSE_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "owner_policy_may_authorize_external_fact_value",
)
BUNDLE_TRUE_FIELDS = (
    "atomicrows_bundle_jsonl_required_for_live_use",
    "atomicrows_bundle_sha_required_for_freeze_authority",
    "atomicrows_bundle_digest_ref_static_placeholder_allowed",
)
BUNDLE_FALSE_FIELDS = (
    "atomicrows_bundle_file_created_by_this_pr",
    "atomicrows_bundle_sha_created_by_this_pr",
    "atomicrows_bundle_hash_authority_created_by_this_pr",
    "atomicrows_bundle_rows_created_by_this_pr",
)
FUTURE_CONSUMER_TRUE_FIELDS = (
    "qtt_trade_context_packet_schema_may_consume",
    "atomicrows_parameter_selection_universe_registry_may_consume",
    "parameter_selection_universe_consumer_gate_may_consume",
    "trade_context_to_selection_universe_routing_gate_may_consume",
    "quantum_applicability_classification_registry_may_consume",
    "owner_quantum_priority_policy_registry_may_consume",
    "scoring_policy_registry_may_consume",
    "parameter_stack_scoring_ranking_gate_may_consume",
    "quantum_classical_optimizer_arbitration_gate_may_consume",
    "candidate_parameter_stack_generation_gate_may_consume",
    "trade_context_parameter_stack_selection_gate_may_consume",
    "selected_parameter_stack_handoff_packet_may_consume",
    "replay_paper_candidate_stack_competition_gate_may_consume",
)
FUTURE_CONSUMER_FALSE_FIELDS = (
    "this_pr_performs_trade_context_schema",
    "this_pr_performs_selection_universe_registry",
    "this_pr_performs_routing",
    "this_pr_performs_scoring",
    "this_pr_performs_ranking",
    "this_pr_performs_selection",
    "this_pr_performs_arbitration",
    "this_pr_generates_candidate_stacks",
    "this_pr_executes_replay_or_paper",
    "this_pr_executes_runtime_or_live",
)
STATIC_POLICY_TRUE_FIELDS = ("selected_stack_id_is_static_schema_field_only",)
STATIC_POLICY_FALSE_FIELDS = (
    "selected_stack_authority_created",
    "stack_selection_created",
    "scoring_created",
    "ranking_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "candidate_stack_generation_created",
    "replay_paper_execution_created",
    "runtime_live_order_authority_created",
    "final_ready_created_by_this_pr",
)
EXPLICIT_NO_CLAIM_FALSE_FIELDS = (
    "selected_stack_authority_created",
    "stack_selection_created",
    "scoring_created",
    "ranking_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "trade_context_packet_created",
    "selection_universe_registry_created",
    "selection_universe_consumer_gate_created",
    "candidate_stack_generation_created",
    "selected_stack_handoff_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "runtime_artifacts_created",
    "runtime_resolver_execution_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "private_state_fetch_created",
    "order_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_results_created",
    "paper_results_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "atomicrows_bundle_rows_created",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "atomicrows_bundle_hash_authority_created",
    "runtime_cash_value_created",
    "connector_semantic_value_created",
    "external_fact_value_created",
    "owner_approval_receipt_created",
    "owner_review_dashboard_runtime_created",
)
PRODUCTION_READINESS_EXPECTED = {
    "edge_parameter_stack_selection_packet_schema_ready": True,
    "production_edge_packet_evaluated": False,
    "production_edge_packet_ready": False,
    "production_stack_selected": False,
    "final_ready": False,
}
FIXTURE_CASE_IDS = (
    "EDGE_PACKET_SCHEMA_VALID_STATIC_ONLY",
    "EDGE_PACKET_BLOCKED_MISSING_SIGNAL_ROLE_FIELD",
    "EDGE_PACKET_BLOCKED_MISSING_QUANTUM_ADVISORY_ROLE_FIELD",
    "EDGE_PACKET_BLOCKED_UPSTREAM_ROLE_INCOMPLETE",
    "EDGE_PACKET_BLOCKED_UPSTREAM_COMPATIBILITY_INCOMPLETE",
    "EDGE_PACKET_BLOCKED_SOURCE_DEPENDENCY_NOT_ACCEPTED",
    "EDGE_PACKET_BLOCKED_BUNDLE_AUTHORITY_ATTEMPT",
    "EDGE_PACKET_BLOCKED_SELECTION_AUTHORITY_ATTEMPT",
    "EDGE_PACKET_BLOCKED_CANDIDATE_GENERATION_ATTEMPT",
    "EDGE_PACKET_BLOCKED_REPLAY_PAPER_EXECUTION_ATTEMPT",
    "EDGE_PACKET_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
    "EDGE_PACKET_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_EDGE_PACKET_READINESS_ONLY",
    "OWNER_GLOBAL_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS_OR_EVIDENCE",
)


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


def _dependency_report_or_validator_ok(
    *,
    root: pathlib.Path,
    report_path: pathlib.Path,
    validator_path: pathlib.Path,
    marker: str,
    label: str,
) -> list[str]:
    report_file = root / report_path
    if report_file.exists():
        try:
            report = load_json(report_file)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return [f"{label}_REPORT_MALFORMED: {exc}"]
        if report.get("validation_marker") == marker:
            return []

    completed = subprocess.run(
        [sys.executable, str(root / validator_path)],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode == 0 and marker in completed.stdout.split():
        return []
    stderr = completed.stderr.strip()
    stdout = completed.stdout.strip()
    return [f"{label}_VALIDATION_BLOCK: marker {marker} missing stdout={stdout!r} stderr={stderr!r}"]


def _roles_from_schema_const(schema: dict[str, Any]) -> list[str]:
    role_schema = _mapping(_mapping(schema.get("properties")).get("required_stack_roles"))
    roles = role_schema.get("const")
    return list(roles) if isinstance(roles, list) else []


def _enum_from_schema(schema: dict[str, Any], def_name: str, property_name: str) -> list[str]:
    definition = _mapping(_mapping(schema.get("$defs")).get(def_name))
    property_schema = _mapping(_mapping(definition.get("properties")).get(property_name))
    enum_values = property_schema.get("enum")
    return list(enum_values) if isinstance(enum_values, list) else []


def validate_pr73_dependency(root: pathlib.Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for label, rel_path in (
        ("PR73_ROLE_TAXONOMY_SCHEMA", PR73_SCHEMA),
        ("PR73_ROLE_TAXONOMY_REGISTRY", PR73_REGISTRY),
        ("PR73_ROLE_TAXONOMY_REPORT", PR73_REPORT),
        ("PR73_ROLE_TAXONOMY_VALIDATOR", PR73_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: {label} missing")
    if failures:
        return list(REQUIRED_STACK_ROLES), failures

    schema = load_json(root / PR73_SCHEMA)
    registry = load_yaml(root / PR73_REGISTRY)
    report = load_json(root / PR73_REPORT)
    roles = registry.get("required_stack_roles")
    if roles != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: registry role order mismatch")
    if _roles_from_schema_const(schema) != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: schema role order mismatch")
    if report.get("validation_marker") != PR73_SUCCESS_MARKER:
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: report marker mismatch")
    if report.get("required_stack_roles_order_valid") is not True:
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: report role order not valid")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR73_REPORT,
            validator_path=PR73_VALIDATOR,
            marker=PR73_SUCCESS_MARKER,
            label="PR73_ROLE_TAXONOMY",
        )
    )
    return list(roles if isinstance(roles, list) else REQUIRED_STACK_ROLES), failures


def validate_pr74_dependency(root: pathlib.Path, pr73_roles: Sequence[str]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for label, rel_path in (
        ("PR74_COMPLETENESS_GATE_SCHEMA", PR74_SCHEMA),
        ("PR74_COMPLETENESS_GATE_REGISTRY", PR74_GATE),
        ("PR74_COMPLETENESS_GATE_REPORT", PR74_REPORT),
        ("PR74_COMPLETENESS_GATE_VALIDATOR", PR74_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: {label} missing")
    if failures:
        return list(pr73_roles), failures

    schema = load_json(root / PR74_SCHEMA)
    gate = load_yaml(root / PR74_GATE)
    report = load_json(root / PR74_REPORT)
    roles = gate.get("required_stack_roles")
    if roles != list(pr73_roles):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: role order differs from PR73")
    if _roles_from_schema_const(schema) != list(REQUIRED_STACK_ROLES):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: schema role order mismatch")
    if _enum_from_schema(schema, "completeness_case", "role_completion_state") != list(
        ROLE_COMPLETION_STATES
    ):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: role state enum mismatch")
    if report.get("validation_marker") != PR74_SUCCESS_MARKER:
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR74_REPORT,
            validator_path=PR74_VALIDATOR,
            marker=PR74_SUCCESS_MARKER,
            label="PR74_COMPLETENESS_GATE",
        )
    )
    return list(roles if isinstance(roles, list) else pr73_roles), failures


def validate_pr75_dependency(root: pathlib.Path, pr74_roles: Sequence[str]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for label, rel_path in (
        ("PR75_COMPATIBILITY_GATE_SCHEMA", PR75_SCHEMA),
        ("PR75_COMPATIBILITY_GATE_REGISTRY", PR75_GATE),
        ("PR75_COMPATIBILITY_GATE_REPORT", PR75_REPORT),
        ("PR75_COMPATIBILITY_GATE_VALIDATOR", PR75_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: {label} missing")
    if failures:
        return list(pr74_roles), failures

    schema = load_json(root / PR75_SCHEMA)
    gate = load_yaml(root / PR75_GATE)
    report = load_json(root / PR75_REPORT)
    roles = gate.get("required_stack_roles")
    if roles != list(pr74_roles):
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: role order differs from PR74")
    if _roles_from_schema_const(schema) != list(REQUIRED_STACK_ROLES):
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: schema role order mismatch")
    if _enum_from_schema(schema, "compatibility_case", "compatibility_state") != list(
        COMPATIBILITY_STATES
    ):
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: compatibility enum mismatch")
    if report.get("validation_marker") != PR75_SUCCESS_MARKER:
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR75_REPORT,
            validator_path=PR75_VALIDATOR,
            marker=PR75_SUCCESS_MARKER,
            label="PR75_COMPATIBILITY_GATE",
        )
    )
    return list(roles if isinstance(roles, list) else pr74_roles), failures


def validate_repair_pr76_dependency(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if not (root / PR76_SHORT_TEST).exists():
        failures.append("PRE_PR77_REPAIR_NOT_APPLIED_BLOCK: repair PR76 short test path missing")
    if (root / PR76_OLD_LONG_TEST).exists():
        failures.append("PRE_PR77_REPAIR_NOT_APPLIED_BLOCK: old long runtime resolver test path exists")
    return failures


def validate_required_role_mapping(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    mapping = _mapping(payload.get("required_stack_role_family_fields"))
    if mapping != ROLE_FAMILY_FIELD_BY_ROLE:
        failures.append(f"{label}.required_stack_role_family_fields must map PR73 roles exactly")
    for role, field in ROLE_FAMILY_FIELD_BY_ROLE.items():
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            failures.append(f"{label}.{role} family field {field} must be an array of strings")
    if "selected_quantum_advisory_family_ids" not in payload:
        failures.append(f"{label}.selected_quantum_advisory_family_ids is required")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["PR77 schema root required must be a list"]
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR77 schema missing required root field {field}")
    if schema.get("additionalProperties") is not False:
        failures.append("PR77 schema must be strict with additionalProperties false")

    properties = _mapping(schema.get("properties"))
    if _mapping(properties.get("authority_class")).get("const") != AUTHORITY_CLASS:
        failures.append("PR77 schema authority_class const mismatch")
    if _mapping(properties.get("packet_id")).get("const") != PACKET_ID:
        failures.append("PR77 schema packet_id const mismatch")
    if _mapping(properties.get("packet_version")).get("const") != PACKET_VERSION:
        failures.append("PR77 schema packet_version const mismatch")
    if _mapping(properties.get("required_stack_role_family_fields")).get("const") != ROLE_FAMILY_FIELD_BY_ROLE:
        failures.append("PR77 schema role family mapping const mismatch")
    if _mapping(properties.get("minimum_required_packet_fields")).get("const") != list(
        MINIMUM_REQUIRED_PACKET_FIELDS
    ):
        failures.append("PR77 schema minimum_required_packet_fields const mismatch")
    if _mapping(properties.get("source_dependency_state")).get("enum") != list(SOURCE_DEPENDENCY_STATES):
        failures.append("PR77 schema source_dependency_state enum mismatch")
    if _mapping(properties.get("atomicrows_bundle_digest_ref")).get("enum") != list(
        ALLOWED_BUNDLE_DIGEST_REFS
    ):
        failures.append("PR77 schema atomicrows_bundle_digest_ref enum mismatch")
    if _mapping(properties.get("role_completion_state")).get("enum") != list(ROLE_COMPLETION_STATES):
        failures.append("PR77 schema role_completion_state enum must match PR74")
    if _mapping(properties.get("compatibility_state")).get("enum") != list(COMPATIBILITY_STATES):
        failures.append("PR77 schema compatibility_state enum must match PR75")
    no_claim_required = _mapping(_mapping(schema.get("$defs")).get("explicit_no_claim_flags")).get("required")
    if no_claim_required != list(EXPLICIT_NO_CLAIM_FALSE_FIELDS):
        failures.append("PR77 schema explicit_no_claim_flags required field order mismatch")
    return failures


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [
        f"{label}{failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def _expect_policy_fields(
    payload: dict[str, Any],
    section: str,
    true_fields: Sequence[str],
    false_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get(section))
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"{label}.{section}.{field} must be true")
    for field in false_fields:
        if policy.get(field) is not False:
            failures.append(f"{label}.{section}.{field} must be false")
    return failures


def validate_owner_override_policy(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("owner_override_policy"))
    if policy.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_supported must be true")
    if policy.get("owner_override_satisfies_internal_edge_packet_readiness_only") is not True:
        failures.append(
            f"{label}.owner_override_satisfies_internal_edge_packet_readiness_only must be true"
        )
    for field in OWNER_OVERRIDE_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_quantum_advisory_boundary(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "quantum_advisory_policy",
        QUANTUM_TRUE_FIELDS,
        QUANTUM_FALSE_FIELDS,
        label,
    )


def validate_source_evidence_boundary(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "source_evidence_boundary_policy",
        SOURCE_TRUE_FIELDS,
        SOURCE_FALSE_FIELDS,
        label,
    )


def validate_atomicrows_bundle_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures = _expect_policy_fields(
        payload,
        "atomicrows_bundle_boundary_policy",
        BUNDLE_TRUE_FIELDS,
        BUNDLE_FALSE_FIELDS,
        label,
    )
    if payload.get("atomicrows_bundle_digest_ref") not in ALLOWED_BUNDLE_DIGEST_REFS:
        failures.append(f"{label}.atomicrows_bundle_digest_ref must be deferred static metadata")
    return failures


def validate_future_consumer_contract(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "future_consumer_contract",
        FUTURE_CONSUMER_TRUE_FIELDS,
        FUTURE_CONSUMER_FALSE_FIELDS,
        label,
    )


def validate_static_packet_policy(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "static_packet_policy",
        STATIC_POLICY_TRUE_FIELDS,
        STATIC_POLICY_FALSE_FIELDS,
        label,
    )


def validate_no_forbidden_flags(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    flags = _mapping(payload.get("explicit_no_claim_flags"))
    for field in EXPLICIT_NO_CLAIM_FALSE_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"{label}.explicit_no_claim_flags.{field} must be false")
    if payload.get("candidate_stack_generation_count") != 0:
        failures.append(f"{label}.candidate_stack_generation_count must remain zero")
    if payload.get("replay_paper_competition_required_flag") is not True:
        failures.append(f"{label}.replay_paper_competition_required_flag must be true")
    if payload.get("owner_review_required_flag") is not True:
        failures.append(f"{label}.owner_review_required_flag must be true")
    if payload.get("final_ready") is not False:
        failures.append(f"{label}.final_ready must be false")
    return failures


def validate_production_packet(
    production_packet: dict[str, Any],
    schema: dict[str, Any],
    expected_roles: Sequence[str],
) -> list[str]:
    failures = schema_subset_failures(production_packet, schema, "production_packet")
    if production_packet.get("packet_id") != PACKET_ID:
        failures.append("production_packet.packet_id mismatch")
    if production_packet.get("packet_version") != PACKET_VERSION:
        failures.append("production_packet.packet_version mismatch")
    if production_packet.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append("production_packet.semantic_task_id mismatch")
    if production_packet.get("authority_class") != AUTHORITY_CLASS:
        failures.append("production_packet.authority_class mismatch")
    if list(expected_roles) != list(REQUIRED_STACK_ROLES):
        failures.append("production_packet upstream required role order mismatch")
    if production_packet.get("minimum_required_packet_fields") != list(MINIMUM_REQUIRED_PACKET_FIELDS):
        failures.append("production_packet.minimum_required_packet_fields mismatch")
    for field in MINIMUM_REQUIRED_PACKET_FIELDS:
        if field not in production_packet:
            failures.append(f"production_packet missing minimum field {field}")
    failures.extend(validate_required_role_mapping(production_packet, "production_packet"))
    failures.extend(validate_owner_override_policy(production_packet, "production_packet"))
    failures.extend(validate_quantum_advisory_boundary(production_packet, "production_packet"))
    failures.extend(validate_source_evidence_boundary(production_packet, "production_packet"))
    failures.extend(validate_atomicrows_bundle_boundary(production_packet, "production_packet"))
    failures.extend(validate_future_consumer_contract(production_packet, "production_packet"))
    failures.extend(validate_static_packet_policy(production_packet, "production_packet"))
    failures.extend(validate_no_forbidden_flags(production_packet, "production_packet"))
    if _mapping(production_packet.get("production_readiness")) != PRODUCTION_READINESS_EXPECTED:
        failures.append("production_packet.production_readiness mismatch")
    return failures


def _base_packet_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    metadata_fields = {"fixture_id", "fixture_version", "mode", "execution", "fixture_cases"}
    return {
        key: copy.deepcopy(value)
        for key, value in fixture.items()
        if key not in metadata_fields
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def case_packet_from_fixture(fixture: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    packet = _deep_merge(_base_packet_from_fixture(fixture), _mapping(case.get("packet_overrides")))
    for field in case.get("missing_fields", []):
        if isinstance(field, str):
            packet.pop(field, None)
    return packet


def _case_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id")): case
        for case in _list_of_mappings(fixture.get("fixture_cases"))
    }


def _normal_packet_ready(packet: dict[str, Any]) -> bool:
    readiness = _mapping(packet.get("production_readiness"))
    return (
        packet.get("role_completion_state") == "ROLE_COMPLETE"
        and packet.get("compatibility_state") == "COMPATIBILITY_COMPLETE"
        and packet.get("source_dependency_state") == "SOURCE_DEPENDENCY_STATIC_DECLARED_NOT_ACCEPTED"
        and packet.get("candidate_stack_generation_count") == 0
        and readiness.get("production_edge_packet_ready") is True
        and packet.get("final_ready") is True
    )


def validate_fixture_cases(fixture: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(fixture, schema, "fixture")
    if fixture.get("fixture_id") != "SYNTHETIC_EDGE_PARAMETER_STACK_SELECTION_PACKET_FIXTURE":
        failures.append("fixture.fixture_id mismatch")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    failures.extend(validate_required_role_mapping(fixture, "fixture"))
    failures.extend(validate_no_forbidden_flags(fixture, "fixture"))

    cases = _case_by_id(fixture)
    if list(cases) != list(FIXTURE_CASE_IDS):
        failures.append("fixture case order or IDs mismatch")
    for case_id in FIXTURE_CASE_IDS:
        case = _mapping(cases.get(case_id))
        if case.get("synthetic_case_only") is not True:
            failures.append(f"{case_id} must be synthetic only")
        packet = case_packet_from_fixture(fixture, case)
        case_failures = schema_subset_failures(packet, schema, case_id)
        expected_schema_valid = case.get("expected_schema_valid")
        if bool(case_failures) == bool(expected_schema_valid):
            failures.append(f"{case_id} schema validity did not match expected")
        if _normal_packet_ready(packet) != case.get("expected_normal_packet_ready"):
            failures.append(f"{case_id} normal packet readiness mismatch")

    if schema_subset_failures(
        case_packet_from_fixture(fixture, _mapping(cases.get("EDGE_PACKET_BLOCKED_MISSING_SIGNAL_ROLE_FIELD"))),
        schema,
        "missing_signal",
    ) == []:
        failures.append("missing selected_signal_family_ids case must fail schema validation")
    if schema_subset_failures(
        case_packet_from_fixture(
            fixture,
            _mapping(cases.get("EDGE_PACKET_BLOCKED_MISSING_QUANTUM_ADVISORY_ROLE_FIELD")),
        ),
        schema,
        "missing_quantum",
    ) == []:
        failures.append("missing selected_quantum_advisory_family_ids case must fail schema validation")

    role_case = case_packet_from_fixture(
        fixture, _mapping(cases.get("EDGE_PACKET_BLOCKED_UPSTREAM_ROLE_INCOMPLETE"))
    )
    if role_case.get("role_completion_state") not in ROLE_COMPLETION_STATES:
        failures.append("role incomplete case must use PR74-compatible state")
    if _normal_packet_ready(role_case):
        failures.append("role incomplete case must block normal packet readiness")

    compatibility_case = case_packet_from_fixture(
        fixture, _mapping(cases.get("EDGE_PACKET_BLOCKED_UPSTREAM_COMPATIBILITY_INCOMPLETE"))
    )
    if compatibility_case.get("compatibility_state") not in COMPATIBILITY_STATES:
        failures.append("compatibility incomplete case must use PR75-compatible state")
    if _normal_packet_ready(compatibility_case):
        failures.append("compatibility incomplete case must block normal packet readiness")

    source_case = case_packet_from_fixture(
        fixture, _mapping(cases.get("EDGE_PACKET_BLOCKED_SOURCE_DEPENDENCY_NOT_ACCEPTED"))
    )
    if (
        source_case.get("source_dependency_state")
        != "SOURCE_DEPENDENCY_ACCEPTED_PACKET_REQUIRED_BEFORE_CONNECTOR_OR_LIVE_USE"
    ):
        failures.append("source dependency case must require accepted packet before connector or live use")
    if _mapping(source_case.get("source_evidence_boundary_policy")).get("accepted_source_packets_created") is not False:
        failures.append("source dependency case must not create accepted source packets")

    override_case = case_packet_from_fixture(
        fixture,
        _mapping(cases.get("OWNER_GLOBAL_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS_OR_EVIDENCE")),
    )
    failures.extend(validate_owner_override_policy(override_case, "owner_override_fixture_case"))
    return failures


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _forbidden_text_patterns() -> tuple[tuple[str, str], ...]:
    return (
        ("REAL_HTTP_LOCATOR", "http" + "://"),
        ("REAL_HTTPS_LOCATOR", "https" + "://"),
        ("REAL_WWW_LOCATOR", "www" + "."),
        ("SECRET_LIKE_API_KEY", "api" + " key"),
        ("SECRET_LIKE_API_KEY_UNDERSCORE", "api" + "_key"),
        ("SECRET_LIKE_PRIVATE_KEY", "private" + " key"),
        ("SECRET_LIKE_BEARER_TOKEN", "bearer" + " token"),
        ("SECRET_LIKE_PASSWORD", "pass" + "word"),
        ("PRIVATE_ACCOUNT_STATE", "private account" + " state"),
        ("ACCOUNT_DATA_CLAIM", "account" + " data"),
        ("EXTERNAL_REPO_CLONE_COMMAND", "git" + " clone"),
        ("PACKAGE_INSTALL_COMMAND_PIP", "pip" + " install"),
        ("PACKAGE_INSTALL_COMMAND_NPM", "npm" + " install"),
        ("LIVE_COMMAND_CLAIM", "live order" + " submitted"),
        ("PROFIT_GUARANTEE_CLAIM", "guaranteed" + " profit"),
        ("PROFIT_RISK_FREE_CLAIM", "risk-free" + " profit"),
        ("QUANTUM_ADVANTAGE_PROOF_CLAIM", "quantum advantage" + " proven"),
        ("QUANTUM_BACKEND_EXECUTION_CLAIM", "backend" + " executed"),
        ("REPLAY_PROOF_CLAIM", "replay passed" + " as proof"),
        ("PAPER_PROOF_CLAIM", "paper passed" + " as proof"),
        ("SOURCE_ACCEPTANCE_CLAIM", "accepted source packet" + " created"),
        ("CONNECTOR_SEMANTIC_CLAIM", "connector semantic binding" + " created"),
        ("BUNDLE_JSONL_CREATION_CLAIM", "AtomicRows.bundle.jsonl" + " created"),
        ("BUNDLE_SHA_CREATION_CLAIM", "AtomicRows.bundle.sha256" + " created"),
        ("RANKED_BEST_STACK_CLAIM", "ranked" + " best stack"),
        ("SELECTED_BEST_STACK_CLAIM", "selected" + " best stack"),
        ("OPTIMIZER_ARBITRATION_RESULT_CLAIM", "optimizer arbitration" + " result"),
        ("TRADE_ROUTED_CLAIM", "trade" + " routed"),
        ("LIVE_ELIGIBLE_CLAIM", "live" + " eligible"),
    )


def _forbidden_text_regexes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    return (("SECRET_LIKE_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),)


def validate_no_forbidden_claims(texts: Sequence[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    for label, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() in lowered:
                failures.append(f"{label}: forbidden static packet text {code}")
        for code, pattern in _forbidden_text_regexes():
            if pattern.search(text):
                failures.append(f"{label}: forbidden static packet text {code}")
    return failures


def validate_no_forbidden_artifacts(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (root / CANONICAL_BUNDLE_JSONL).exists():
        failures.append("ATOMICROWS_BUNDLE_FORBIDDEN_ARTIFACT_BLOCK")
    if (root / CANONICAL_BUNDLE_SHA256).exists():
        failures.append("ATOMICROWS_BUNDLE_SHA_FORBIDDEN_ARTIFACT_BLOCK")
    return failures


def validate_master_plan_not_modified(root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "--", str(MASTER_PLAN_CURRENT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR77"]
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {completed.stderr.strip()}"]


def _flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("explicit_no_claim_flags")).get(field))


def _policy_flag(payload: dict[str, Any], section: str, field: str) -> bool:
    return bool(_mapping(payload.get(section)).get(field))


def build_report(
    *,
    root: pathlib.Path,
    production_packet: dict[str, Any],
    schema_path: pathlib.Path,
    production_packet_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    readiness = _mapping(production_packet.get("production_readiness"))
    bundle_policy = _mapping(production_packet.get("atomicrows_bundle_boundary_policy"))
    source_policy = _mapping(production_packet.get("source_evidence_boundary_policy"))
    quantum_policy = _mapping(production_packet.get("quantum_advisory_policy"))
    owner_policy = _mapping(production_packet.get("owner_override_policy"))
    return {
        "accepted_source_packets_created": source_policy.get("accepted_source_packets_created")
        or _flag(production_packet, "accepted_source_packets_created"),
        "all_required_role_family_fields_present": (
            _mapping(production_packet.get("required_stack_role_family_fields"))
            == ROLE_FAMILY_FIELD_BY_ROLE
        ),
        "atomicrows_bundle_digest_ref_required": "atomicrows_bundle_digest_ref"
        in production_packet.get("minimum_required_packet_fields", []),
        "atomicrows_bundle_digest_ref_static_placeholder_allowed": bundle_policy.get(
            "atomicrows_bundle_digest_ref_static_placeholder_allowed"
        ),
        "atomicrows_bundle_hash_authority_created": bundle_policy.get(
            "atomicrows_bundle_hash_authority_created_by_this_pr"
        )
        or _flag(production_packet, "atomicrows_bundle_hash_authority_created"),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "candidate_stack_generation_created": _flag(
            production_packet, "candidate_stack_generation_created"
        ),
        "cash_receipts_created": _flag(production_packet, "cash_receipts_created"),
        "connector_semantic_binding_created": _flag(
            production_packet, "connector_semantic_binding_created"
        ),
        "connector_semantics_created": _flag(production_packet, "connector_semantics_created"),
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "edge_parameter_stack_selection_packet_schema_ready": readiness.get(
            "edge_parameter_stack_selection_packet_schema_ready"
        ),
        "execution_superiority_claim_created": _flag(
            production_packet, "execution_superiority_claim_created"
        ),
        "fallback_bundle_required_before_quantum_runtime_use": quantum_policy.get(
            "fallback_bundle_required_before_quantum_runtime_use"
        ),
        "fill_receipts_created": _flag(production_packet, "fill_receipts_created"),
        "final_ready": production_packet.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": quantum_policy.get(
            "future_optimizer_arbitration_gate_required_before_optimizer_choice"
        ),
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": quantum_policy.get(
            "future_owner_quantum_priority_policy_required_before_quantum_priority_selection"
        ),
        "future_quantum_applicability_registry_required_before_quantum_selection": quantum_policy.get(
            "future_quantum_applicability_registry_required_before_quantum_selection"
        ),
        "latency_superiority_claim_created": _flag(
            production_packet, "latency_superiority_claim_created"
        ),
        "live_evidence_required_before_profit_claim": quantum_policy.get(
            "live_evidence_required_before_profit_claim"
        ),
        "live_readiness_created": _flag(production_packet, "live_readiness_created"),
        "optimizer_arbitration_created": _flag(
            production_packet, "optimizer_arbitration_created"
        ),
        "order_authority_created": _flag(production_packet, "order_authority_created"),
        "order_receipts_created": _flag(production_packet, "order_receipts_created"),
        "owner_override_fabricates_accepted_source_packet": owner_policy.get(
            "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_connector_semantic": owner_policy.get(
            "owner_override_fabricates_connector_semantic"
        ),
        "owner_override_fabricates_external_fact": owner_policy.get(
            "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": owner_policy.get(
            "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": owner_policy.get(
            "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": owner_policy.get(
            "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": owner_policy.get(
            "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": owner_policy.get(
            "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_satisfies_internal_edge_packet_readiness_only": owner_policy.get(
            "owner_override_satisfies_internal_edge_packet_readiness_only"
        ),
        "paper_execution_created": _flag(production_packet, "paper_execution_created"),
        "paper_results_created": _flag(production_packet, "paper_results_created"),
        "private_state_fetch_created": _flag(production_packet, "private_state_fetch_created"),
        "production_edge_packet_evaluated": readiness.get("production_edge_packet_evaluated"),
        "production_edge_packet_ready": readiness.get("production_edge_packet_ready"),
        "production_packet_path": _as_posix(production_packet_path),
        "production_stack_selected": readiness.get("production_stack_selected"),
        "profit_evidence_created": _flag(production_packet, "profit_evidence_created"),
        "quantum_advantage_claim_created": quantum_policy.get("quantum_advantage_claim_created")
        or _flag(production_packet, "quantum_advantage_claim_created"),
        "quantum_advisory_static_metadata_only": quantum_policy.get(
            "quantum_advisory_static_metadata_only"
        ),
        "quantum_backend_evidence_created": _flag(
            production_packet, "quantum_backend_evidence_created"
        ),
        "ranking_created": _flag(production_packet, "ranking_created"),
        "replay_execution_created": _flag(production_packet, "replay_execution_created"),
        "replay_paper_evidence_required_before_advantage_claim": quantum_policy.get(
            "replay_paper_evidence_required_before_advantage_claim"
        ),
        "replay_results_created": _flag(production_packet, "replay_results_created"),
        "repair_pr76_long_path_fix_present": (root / PR76_SHORT_TEST).exists()
        and not (root / PR76_OLD_LONG_TEST).exists(),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_stack_role_count": len(REQUIRED_STACK_ROLES),
        "required_stack_roles_order_valid": True,
        "runtime_artifacts_created": _flag(production_packet, "runtime_artifacts_created"),
        "runtime_live_use_created": _flag(production_packet, "runtime_live_use_created"),
        "runtime_resolver_execution_created": _flag(
            production_packet, "runtime_resolver_execution_created"
        ),
        "schema_path": _as_posix(schema_path),
        "scoring_created": _flag(production_packet, "scoring_created"),
        "selected_quantum_advisory_family_ids_required": "selected_quantum_advisory_family_ids"
        in production_packet.get("minimum_required_packet_fields", []),
        "selected_stack_authority_created": _flag(
            production_packet, "selected_stack_authority_created"
        ),
        "selected_stack_handoff_created": _flag(
            production_packet, "selected_stack_handoff_created"
        ),
        "selection_universe_registry_created": _flag(
            production_packet, "selection_universe_registry_created"
        ),
        "source_acceptance_created": source_policy.get("source_acceptance_created")
        or _flag(production_packet, "source_acceptance_created"),
        "source_dependency_state_required": "source_dependency_state"
        in production_packet.get("minimum_required_packet_fields", []),
        "source_dependency_state_static_metadata_only": source_policy.get(
            "source_dependency_state_is_static_metadata_only"
        ),
        "source_retrieval_created": source_policy.get("source_retrieval_created")
        or _flag(production_packet, "source_retrieval_created"),
        "stack_selection_created": _flag(production_packet, "stack_selection_created"),
        "strongest_classical_comparator_required_before_quantum_advantage_claim": quantum_policy.get(
            "strongest_classical_comparator_required_before_quantum_advantage_claim"
        ),
        "trade_context_packet_created": _flag(production_packet, "trade_context_packet_created"),
        "trade_context_routing_created": _flag(
            production_packet, "trade_context_routing_created"
        ),
        "validation_marker": SUCCESS_MARKER,
        "validator": VALIDATOR_NAME,
    }


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "repair_pr76_long_path_fix_present": True,
        "required_stack_role_count": len(REQUIRED_STACK_ROLES),
        "required_stack_roles_order_valid": True,
        "all_required_role_family_fields_present": True,
        "selected_quantum_advisory_family_ids_required": True,
        "edge_parameter_stack_selection_packet_schema_ready": True,
        "production_edge_packet_evaluated": False,
        "production_edge_packet_ready": False,
        "production_stack_selected": False,
        "final_ready": False,
        "atomicrows_bundle_digest_ref_required": True,
        "atomicrows_bundle_digest_ref_static_placeholder_allowed": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "atomicrows_bundle_hash_authority_created": False,
        "source_dependency_state_required": True,
        "source_dependency_state_static_metadata_only": True,
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "accepted_source_packets_created": False,
        "connector_semantics_created": False,
        "connector_semantic_binding_created": False,
        "selected_stack_authority_created": False,
        "stack_selection_created": False,
        "scoring_created": False,
        "ranking_created": False,
        "optimizer_arbitration_created": False,
        "trade_context_routing_created": False,
        "trade_context_packet_created": False,
        "selection_universe_registry_created": False,
        "candidate_stack_generation_created": False,
        "selected_stack_handoff_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_results_created": False,
        "paper_results_created": False,
        "runtime_artifacts_created": False,
        "runtime_resolver_execution_created": False,
        "live_readiness_created": False,
        "runtime_live_use_created": False,
        "private_state_fetch_created": False,
        "order_authority_created": False,
        "cash_receipts_created": False,
        "order_receipts_created": False,
        "fill_receipts_created": False,
        "profit_evidence_created": False,
        "quantum_advisory_static_metadata_only": True,
        "future_quantum_applicability_registry_required_before_quantum_selection": True,
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": True,
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": True,
        "strongest_classical_comparator_required_before_quantum_advantage_claim": True,
        "fallback_bundle_required_before_quantum_runtime_use": True,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
        "quantum_backend_evidence_created": False,
        "quantum_advantage_claim_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "owner_override_satisfies_internal_edge_packet_readiness_only": True,
        "owner_override_fabricates_external_fact": False,
        "owner_override_fabricates_accepted_source_packet": False,
        "owner_override_fabricates_connector_semantic": False,
        "owner_override_fabricates_runtime_cash_receipt": False,
        "owner_override_fabricates_order_receipt": False,
        "owner_override_fabricates_replay_paper_result": False,
        "owner_override_fabricates_quantum_backend_execution": False,
        "owner_override_fabricates_profit_evidence": False,
        "validation_marker": SUCCESS_MARKER,
    }
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is not deterministic sorted JSON")
    return failures


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate(
    *,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    production_packet_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    pr73_roles, pr73_failures = validate_pr73_dependency(root)
    failures.extend(pr73_failures)
    pr74_roles, pr74_failures = validate_pr74_dependency(root, pr73_roles)
    failures.extend(pr74_failures)
    pr75_roles, pr75_failures = validate_pr75_dependency(root, pr74_roles)
    failures.extend(pr75_failures)
    if pr75_roles != list(REQUIRED_STACK_ROLES):
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: role order mismatch")
    failures.extend(validate_repair_pr76_dependency(root))

    schema, schema_failures = _load_json_checked(root / schema_path, "PR77_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_packet = load_yaml(root / production_packet_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR77_PRODUCTION_PACKET_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR77_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        failures.extend(validate_production_packet(production_packet, schema, pr75_roles))
        failures.extend(validate_fixture_cases(fixture, schema))
    else:
        failures.extend(validate_required_role_mapping(production_packet, "production_packet"))
        failures.extend(validate_required_role_mapping(fixture, "fixture"))

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_packet_path), _read_text(root / production_packet_path)),
        (_as_posix(fixture_path), _read_text(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        production_packet=production_packet,
        schema_path=schema_path,
        production_packet_path=production_packet_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        production_packet=production_packet,
        schema_path=schema_path,
        production_packet_path=production_packet_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR77 report is not deterministic")
    failures.extend(validate_no_forbidden_claims((("generated_report", serialize_report(report)),)))
    failures.extend(_report_safety_failures(report))

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-packet", default=str(DEFAULT_PRODUCTION_PACKET))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_packet_path=pathlib.Path(args.production_packet),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    print(FAILURE_MARKER)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
