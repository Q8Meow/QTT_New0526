#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_qtt_agent_algorithm_binding_registry as binding_gate  # noqa: E402
from tools import validate_qtt_agent_algorithm_consumer_gate as consumer_gate  # noqa: E402
from tools import validate_qtt_algorithm_formula_family_registry as algorithm_gate  # noqa: E402
from tools import validate_qtt_owner_global_override_authority as owner_authority  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "agent_algorithm"
    / "qtt_agent_algorithm_cumulative_readiness_gate.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agent_algorithm"
    / "QTTAgentAlgorithmCumulativeReadinessGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "agent_algorithm"
    / "synthetic_qtt_agent_algorithm_cumulative_readiness_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
)

MASTER_PLAN = binding_gate.MASTER_PLAN
AGENT_CHARTER_REGISTRY = binding_gate.AGENT_CHARTER_REGISTRY
ALGORITHM_FORMULA_FAMILY_REGISTRY = binding_gate.ALGORITHM_FORMULA_FAMILY_REGISTRY
AGENT_ALGORITHM_BINDING_REGISTRY = binding_gate.DEFAULT_REGISTRY
AGENT_ALGORITHM_CONSUMER_GATE = consumer_gate.DEFAULT_REGISTRY
OWNER_GLOBAL_OVERRIDE_REPORT = owner_authority.DEFAULT_REPORT
AGENT_ROLE_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentRoleOperatingCharterReport.json"
)
ALGORITHM_FORMULA_FAMILY_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAlgorithmFormulaFamilyReport.json"
)
AGENT_ALGORITHM_BINDING_REPORT = binding_gate.DEFAULT_REPORT
AGENT_ALGORITHM_CONSUMER_GATE_REPORT = consumer_gate.DEFAULT_REPORT
CANONICAL_BUNDLE = binding_gate.CANONICAL_BUNDLE
CANONICAL_BUNDLE_SHA = binding_gate.CANONICAL_BUNDLE_SHA

REGISTRY_TYPE = "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE"
REGISTRY_VERSION = "v1"
REPORT_TYPE = "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = binding_gate.DETERMINISTIC_GENERATED_AT
READINESS_GENERATION_POLICY = (
    "CUMULATIVE_STATIC_FOUNDATION_FROM_OWNER_AGENT_ALGORITHM_BINDING_AND_CONSUMER_GATE_ARTIFACTS"
)
ARCHITECTURE_EMPHASIS = (
    "INSTITUTIONAL_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_NOT_FINAL_READINESS"
)
OWNER_OVERRIDE_SATISFACTION_BASIS = (
    "OWNER_GLOBAL_OVERRIDE_SATISFIES_QTT_INTERNAL_WORKFLOW_REQUIREMENTS_WITHOUT_FABRICATING_EXTERNAL_FACTS_OR_EVIDENCE"
)
STATIC_FORWARD_REFERENCE_ONLY = binding_gate.STATIC_FORWARD_REFERENCE_ONLY
SUCCESS_MARKER = "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_OK"
FAILURE_MARKER = "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FINAL_INCOMPLETE"
)

COMPONENT_IDS = (
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_001_OWNER_GLOBAL_OVERRIDE_AUTHORITY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_002_AGENT_ROLE_OPERATING_CHARTER_REGISTRY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_003_ALGORITHM_FORMULA_FAMILY_REGISTRY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_004_AGENT_ALGORITHM_BINDING_REGISTRY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_005_AGENT_ALGORITHM_CONSUMER_GATE",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_006_QUANTUM_FORWARD_COMPATIBILITY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_007_STATIC_NO_RUNTIME_NO_EVIDENCE_BOUNDARY",
    "QTT_AGENT_ALGORITHM_CUMULATIVE_COMPONENT_008_FUTURE_PR_DEPENDENCY_BOUNDARY",
)

TOP_FIELDS = (
    "registry_type",
    "registry_version",
    "deterministic_output",
    "generated_at_utc",
    "source_of_readiness_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "agent_algorithm_binding_registry_dependency",
    "agent_algorithm_consumer_gate_dependency",
    "owner_global_override_report_dependency",
    "agent_role_report_dependency",
    "algorithm_formula_family_report_dependency",
    "agent_algorithm_binding_report_dependency",
    "agent_algorithm_consumer_gate_report_dependency",
    "readiness_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_override_satisfies_agent_algorithm_readiness",
    "static_agent_algorithm_foundation_ready",
    "normal_static_agent_algorithm_coverage_ready",
    "normal_full_agent_algorithm_coverage_ready",
    "qtt_internal_agent_algorithm_ready",
    "future_command_matrix_required",
    "agent_algorithm_command_matrix_created",
    "future_parameter_stack_layers_required",
    "future_scoring_ranking_layers_required",
    "future_quantum_classical_arbitration_required",
    "future_replay_paper_evidence_required",
    "future_runtime_live_readiness_required",
    "future_atomicrows_bundle_hash_required",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "static_agent_algorithm_cumulative_readiness_gate_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "readiness_components",
)

FIXTURE_EXTRA_FIELDS = (
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "mode",
    "execution",
)

COMPONENT_FIELDS = (
    "component_id",
    "component_name",
    "component_category",
    "component_description",
    "dependency_paths",
    "dependency_reports",
    "expected_success_markers",
    "measured_counts",
    "component_present",
    "component_validated",
    "static_foundation_contribution",
    "owner_override_supported",
    "owner_override_satisfaction_basis",
    "qtt_internal_ready_contribution",
    "normal_static_ready_contribution",
    "normal_full_ready_contribution",
    "final_ready_contribution",
    "quantum_forward_contribution",
    "future_pr_dependency_reason",
    "evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_evidence_claim_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "reason_codes",
)

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_readiness_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "agent_algorithm_binding_registry_dependency",
    "agent_algorithm_consumer_gate_dependency",
    "owner_global_override_report_dependency",
    "agent_role_report_dependency",
    "algorithm_formula_family_report_dependency",
    "agent_algorithm_binding_report_dependency",
    "agent_algorithm_consumer_gate_report_dependency",
    "readiness_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "architecture_emphasis",
    "component_count",
    "required_component_count",
    "components_present_count",
    "missing_component_count",
    "invalid_component_order_count",
    "agent_role_count_from_charter_registry",
    "algorithm_family_count_from_algorithm_registry",
    "binding_count_from_binding_registry",
    "expected_binding_count_from_binding_report",
    "consumer_allowed_attempt_count",
    "consumer_blocked_attempt_count",
    "consumer_owner_override_attempt_count",
    "invalid_agent_role_count",
    "invalid_algorithm_family_count",
    "invalid_binding_count",
    "invalid_consumer_authorization_count",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_override_satisfies_agent_algorithm_readiness",
    "static_agent_algorithm_foundation_ready",
    "normal_static_agent_algorithm_coverage_ready",
    "normal_full_agent_algorithm_coverage_ready",
    "qtt_internal_agent_algorithm_ready",
    "future_command_matrix_required",
    "agent_algorithm_command_matrix_created",
    "future_parameter_stack_layers_required",
    "future_scoring_ranking_layers_required",
    "future_quantum_classical_arbitration_required",
    "future_replay_paper_evidence_required",
    "future_runtime_live_readiness_required",
    "future_atomicrows_bundle_hash_required",
    "quantum_forward_design_supported",
    "quantum_algorithm_family_count",
    "quantum_binding_count",
    "quantum_consumer_allowed_attempt_count",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority_supported",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_evidence_claim_created",
    "static_agent_algorithm_cumulative_readiness_gate_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "authority_boundary_all_false",
)

FALSE_ARTIFACT_AND_EVIDENCE_FIELDS = (
    "evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "profit_artifact_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_evidence_claim_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "real_runtime_artifact_created",
    "real_live_artifact_created",
    "real_order_artifact_created",
    "real_profit_artifact_created",
    "real_quantum_backend_artifact_created",
    "external_fact_claim_created",
    "private_state_fetch_created",
    "secret_materialization_created",
    "package_install_created",
    "external_repo_clone_created",
)

TOP_FALSE_FIELDS = (
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "agent_algorithm_command_matrix_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
)

TOP_TRUE_FIELDS = (
    "deterministic_output",
    "master_plan_followed_as_controlling_doctrine",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_override_satisfies_agent_algorithm_readiness",
    "static_agent_algorithm_foundation_ready",
    "normal_static_agent_algorithm_coverage_ready",
    "qtt_internal_agent_algorithm_ready",
    "future_command_matrix_required",
    "future_parameter_stack_layers_required",
    "future_scoring_ranking_layers_required",
    "future_quantum_classical_arbitration_required",
    "future_replay_paper_evidence_required",
    "future_runtime_live_readiness_required",
    "future_atomicrows_bundle_hash_required",
    "quantum_forward_design_supported",
    "static_agent_algorithm_cumulative_readiness_gate_created",
)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def serialize_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_json(value), encoding="utf-8")


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    return binding_gate.load_registry(path)


def _normalize_path(path: pathlib.Path | str) -> str:
    return str(path).replace("\\", "/")


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _load_registry(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    return binding_gate._load_registry(path)


def _int(mapping: Mapping[str, Any] | None, field: str) -> int:
    value = (mapping or {}).get(field)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _bool(mapping: Mapping[str, Any] | None, field: str) -> bool:
    return (mapping or {}).get(field) is True


def _items(value: Mapping[str, Any] | None, field: str) -> list[dict[str, Any]]:
    items = (value or {}).get(field)
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _has_forbidden_true(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FALSE_ARTIFACT_AND_EVIDENCE_FIELDS and item is True:
                return True
            if _has_forbidden_true(item):
                return True
    elif isinstance(value, list):
        return any(_has_forbidden_true(item) for item in value)
    return False


def _command_matrix_paths(repo_root: pathlib.Path) -> tuple[pathlib.Path, ...]:
    return (
        repo_root
        / "docs"
        / "master_plan"
        / "agent_algorithm"
        / "QTTAgentAlgorithmCommandMatrix.yaml",
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "QTTAgentAlgorithmCommandMatrix.json",
    )


def _binding_count_from_algorithm_authorized_roles(
    algorithm_families: Sequence[dict[str, Any]],
) -> int:
    total = 0
    for family in algorithm_families:
        roles = family.get("authorized_agent_roles")
        if isinstance(roles, list):
            total += len([role for role in roles if isinstance(role, str) and role])
    return total


def collect_metrics(
    *,
    repo_root: pathlib.Path,
    registry: dict[str, Any] | None,
    owner_report: dict[str, Any] | None,
    agent_registry: dict[str, Any] | None,
    algorithm_registry: dict[str, Any] | None,
    binding_registry: dict[str, Any] | None,
    consumer_registry: dict[str, Any] | None,
    agent_report: dict[str, Any] | None,
    algorithm_report: dict[str, Any] | None,
    binding_report: dict[str, Any] | None,
    consumer_report: dict[str, Any] | None,
) -> dict[str, Any]:
    charters_by_role, _ = binding_gate._agent_charters_by_role(agent_registry)
    families_by_name, algorithm_families, _ = binding_gate._algorithm_families_by_name(
        algorithm_registry
    )
    _, bindings, _ = consumer_gate._bindings_by_id(binding_registry)
    attempts = _items(consumer_registry, "consumer_attempts")
    allowed = [
        attempt
        for attempt in attempts
        if attempt.get("attempt_type") == consumer_gate.ATTEMPT_TYPE_ALLOWED
    ]
    blocked = [attempt for attempt in attempts if attempt.get("gate_decision") == "BLOCK"]
    owner_override = [
        attempt
        for attempt in attempts
        if attempt.get("gate_decision")
        == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW"
    ]
    quantum_families = [
        family
        for family in algorithm_families
        if family.get("algorithm_family_name")
        in algorithm_gate.QUANTUM_OR_COMPATIBLE_FAMILY_NAMES
    ]
    quantum_bindings = [
        binding
        for binding in bindings
        if binding_gate._family_is_quantum_or_compatible(
            families_by_name.get(str(binding.get("algorithm_family_name")), {})
        )
    ]
    quantum_allowed = [
        attempt
        for attempt in allowed
        if consumer_gate._is_quantum_or_quantum_compatible(attempt)
    ]
    components = _items(registry, "readiness_components")
    invalid_order = 0 if [c.get("component_id") for c in components] == list(COMPONENT_IDS) else 1
    command_matrix_present = any(path.exists() for path in _command_matrix_paths(repo_root))
    bundle_file_present = (repo_root / CANONICAL_BUNDLE).exists()
    bundle_sha_present = (repo_root / CANONICAL_BUNDLE_SHA).exists()

    invalid_agent_role_count = (
        _int(agent_report, "missing_agent_role_count")
        + _int(binding_report, "invalid_agent_role_count")
        + _int(binding_report, "invalid_agent_role_id_count")
        + _int(consumer_report, "invalid_agent_role_attempt_count")
    )
    invalid_algorithm_family_count = (
        _int(algorithm_report, "missing_algorithm_family_count")
        + _int(binding_report, "invalid_algorithm_family_count")
        + _int(binding_report, "invalid_algorithm_family_id_count")
        + _int(consumer_report, "invalid_algorithm_family_attempt_count")
    )
    invalid_binding_count = (
        _int(binding_report, "missing_binding_count")
        + _int(binding_report, "duplicate_binding_id_count")
        + _int(consumer_report, "invalid_binding_attempt_count")
        + _int(consumer_report, "missing_allowed_attempt_count")
        + _int(consumer_report, "unexpected_allowed_attempt_count")
        + _int(consumer_report, "attempts_with_duplicate_id_count")
    )
    invalid_consumer_authorization_count = (
        _int(consumer_report, "invalid_consumer_class_authorization_count")
        + _int(consumer_report, "invalid_trade_context_authorization_count")
        + _int(consumer_report, "owner_override_attempts_fabricating_binding_rows_count")
        + _int(consumer_report, "owner_override_attempts_without_satisfaction_count")
    )

    owner_override_ready = (
        _bool(owner_report, "owner_global_override_authority")
        and _bool(owner_report, "owner_override_satisfies_all_qtt_internal_requirements")
        and owner_report is not None
        and owner_report.get("chatgpt_authority_over_owner") is False
        and owner_report.get("codex_authority_over_owner") is False
        and owner_report.get("qtt_agent_authority_over_owner") is False
        and _int(owner_report, "owner_override_blocked_case_count") == 0
        and _int(owner_report, "validators_block_owner_override_count") == 0
        and _int(owner_report, "generated_reports_block_owner_override_count") == 0
        and _int(owner_report, "validation_gates_block_owner_override_count") == 0
    )
    agent_ready = (
        len(charters_by_role) == 25
        and _int(agent_report, "agent_role_count") == 25
        and _int(agent_report, "required_agent_roles_present_count") == 25
        and invalid_agent_role_count == 0
        and agent_report is not None
    )
    algorithm_ready = (
        len(algorithm_families) == 15
        and _int(algorithm_report, "algorithm_family_count") == 15
        and _int(algorithm_report, "required_algorithm_families_present_count") == 15
        and invalid_algorithm_family_count == 0
        and algorithm_report is not None
    )
    expected_from_algorithm = _binding_count_from_algorithm_authorized_roles(
        algorithm_families
    )
    expected_from_binding_report = _int(
        binding_report, "expected_binding_count_from_algorithm_registry_authorized_roles"
    )
    binding_ready = (
        len(bindings) == expected_from_algorithm
        and len(bindings) == expected_from_binding_report
        and _int(binding_report, "actual_binding_count") == len(bindings)
        and invalid_binding_count == 0
        and binding_report is not None
    )
    consumer_ready = (
        len(allowed) == len(bindings)
        and _int(consumer_report, "actual_allowed_attempt_count") == len(bindings)
        and _int(consumer_report, "expected_allowed_attempt_count_from_binding_registry")
        == len(bindings)
        and len(blocked) >= 5
        and len(owner_override) >= 5
        and _int(consumer_report, "blocked_attempt_count") >= 5
        and _int(consumer_report, "owner_override_attempt_count") >= 5
        and invalid_consumer_authorization_count == 0
        and consumer_report is not None
    )
    upstream_reports = (
        owner_report,
        agent_report,
        algorithm_report,
        binding_report,
        consumer_report,
    )
    upstream_final_ready_true = any(
        report.get("final_ready") is True
        for report in upstream_reports
        if isinstance(report, dict)
    )
    forbidden_artifact_true = any(
        _has_forbidden_true(value)
        for value in (
            registry,
            owner_report,
            agent_report,
            algorithm_report,
            binding_report,
            consumer_report,
        )
        if isinstance(value, dict)
    )
    authority_boundary_all_false = (
        owner_override_ready
        and all(
            report.get("authority_boundary_all_false") is True
            for report in (owner_report, agent_report, algorithm_report, binding_report, consumer_report)
            if isinstance(report, dict) and "authority_boundary_all_false" in report
        )
        and not forbidden_artifact_true
        and not upstream_final_ready_true
        and not command_matrix_present
        and not bundle_file_present
        and not bundle_sha_present
    )
    quantum_forward_supported = (
        _bool(algorithm_report, "quantum_forward_design_supported")
        and _bool(binding_report, "quantum_forward_design_supported")
        and _bool(consumer_report, "quantum_forward_design_supported")
        and len(quantum_families) >= 9
        and len(quantum_bindings) >= 1
        and len(quantum_allowed) >= 1
        and not forbidden_artifact_true
    )
    owner_quantum_priority_supported = (
        quantum_forward_supported
        and _int(algorithm_report, "owner_quantum_priority_supported_count")
        >= _int(algorithm_report, "quantum_or_quantum_compatible_algorithm_family_count")
        and _int(binding_report, "quantum_bindings_with_owner_quantum_priority_supported_count")
        == len(quantum_bindings)
        and _int(consumer_report, "quantum_allowed_attempts_with_owner_quantum_priority_supported_count")
        == len(quantum_allowed)
    )
    owner_can_force_quantum_priority_supported = (
        quantum_forward_supported
        and _int(algorithm_report, "owner_can_force_quantum_priority_count")
        >= _int(algorithm_report, "quantum_or_quantum_compatible_algorithm_family_count")
        and _int(binding_report, "quantum_bindings_with_owner_can_force_quantum_priority_count")
        == len(quantum_bindings)
        and _int(consumer_report, "quantum_allowed_attempts_with_owner_can_force_quantum_priority_count")
        == len(quantum_allowed)
    )
    static_foundation_ready = (
        owner_override_ready
        and agent_ready
        and algorithm_ready
        and binding_ready
        and consumer_ready
        and authority_boundary_all_false
        and quantum_forward_supported
    )
    owner_override_satisfies_agent_algorithm_readiness = (
        owner_override_ready
        and _bool(owner_report, "owner_override_applies_to_all_qtt_internal_requirements")
        and _bool(owner_report, "owner_override_applies_to_missing_required_values")
    )
    normal_static_ready = (
        static_foundation_ready
        and not command_matrix_present
        and not bundle_file_present
        and not bundle_sha_present
    )
    normal_full_ready = False
    qtt_internal_ready = (
        static_foundation_ready and owner_override_satisfies_agent_algorithm_readiness
    )
    return {
        "component_count": len(components),
        "required_component_count": len(COMPONENT_IDS),
        "components_present_count": sum(1 for component in components if component.get("component_present") is True),
        "missing_component_count": max(len(COMPONENT_IDS) - len(components), 0),
        "invalid_component_order_count": invalid_order,
        "agent_role_count_from_charter_registry": len(charters_by_role),
        "algorithm_family_count_from_algorithm_registry": len(algorithm_families),
        "binding_count_from_binding_registry": len(bindings),
        "expected_binding_count_from_algorithm_registry": expected_from_algorithm,
        "expected_binding_count_from_binding_report": expected_from_binding_report,
        "consumer_allowed_attempt_count": len(allowed),
        "consumer_blocked_attempt_count": len(blocked),
        "consumer_owner_override_attempt_count": len(owner_override),
        "invalid_agent_role_count": invalid_agent_role_count,
        "invalid_algorithm_family_count": invalid_algorithm_family_count,
        "invalid_binding_count": invalid_binding_count,
        "invalid_consumer_authorization_count": invalid_consumer_authorization_count,
        "owner_global_override_authority": owner_override_ready,
        "owner_override_satisfies_all_qtt_internal_requirements": _bool(
            owner_report, "owner_override_satisfies_all_qtt_internal_requirements"
        ),
        "owner_override_satisfies_agent_algorithm_readiness": owner_override_satisfies_agent_algorithm_readiness,
        "static_agent_algorithm_foundation_ready": static_foundation_ready,
        "normal_static_agent_algorithm_coverage_ready": normal_static_ready,
        "normal_full_agent_algorithm_coverage_ready": normal_full_ready,
        "qtt_internal_agent_algorithm_ready": qtt_internal_ready,
        "quantum_forward_design_supported": quantum_forward_supported,
        "quantum_algorithm_family_count": len(quantum_families),
        "quantum_binding_count": len(quantum_bindings),
        "quantum_consumer_allowed_attempt_count": len(quantum_allowed),
        "owner_quantum_priority_supported": owner_quantum_priority_supported,
        "owner_can_force_quantum_priority_supported": owner_can_force_quantum_priority_supported,
        "bundle_file_present": bundle_file_present,
        "bundle_sha_present": bundle_sha_present,
        "agent_algorithm_command_matrix_created": command_matrix_present,
        "authority_boundary_all_false": authority_boundary_all_false,
        "upstream_final_ready_true": upstream_final_ready_true,
        "forbidden_artifact_true": forbidden_artifact_true,
    }


def _component(
    *,
    component_id: str,
    component_name: str,
    component_category: str,
    component_description: str,
    dependency_paths: Sequence[pathlib.Path | str],
    dependency_reports: Sequence[pathlib.Path | str],
    expected_success_markers: Sequence[str],
    measured_counts: Mapping[str, Any],
    component_present: bool,
    component_validated: bool,
    static_foundation_contribution: bool,
    qtt_internal_ready_contribution: bool,
    normal_static_ready_contribution: bool,
    normal_full_ready_contribution: bool,
    final_ready_contribution: bool,
    quantum_forward_contribution: bool,
    future_pr_dependency_reason: str,
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    component = {
        "component_id": component_id,
        "component_name": component_name,
        "component_category": component_category,
        "component_description": component_description,
        "dependency_paths": [_normalize_path(path) for path in dependency_paths],
        "dependency_reports": [_normalize_path(path) for path in dependency_reports],
        "expected_success_markers": list(expected_success_markers),
        "measured_counts": dict(measured_counts),
        "component_present": component_present,
        "component_validated": component_validated,
        "static_foundation_contribution": static_foundation_contribution,
        "owner_override_supported": True,
        "owner_override_satisfaction_basis": OWNER_OVERRIDE_SATISFACTION_BASIS,
        "qtt_internal_ready_contribution": qtt_internal_ready_contribution,
        "normal_static_ready_contribution": normal_static_ready_contribution,
        "normal_full_ready_contribution": normal_full_ready_contribution,
        "final_ready_contribution": final_ready_contribution,
        "quantum_forward_contribution": quantum_forward_contribution,
        "future_pr_dependency_reason": future_pr_dependency_reason,
        "evidence_claim_created": False,
        "alpha_evidence_claim_created": False,
        "profit_evidence_claim_created": False,
        "latency_superiority_evidence_claim_created": False,
        "execution_superiority_evidence_claim_created": False,
        "quantum_evidence_claim_created": False,
        "runtime_artifact_created": False,
        "live_artifact_created": False,
        "order_artifact_created": False,
        "source_acceptance_artifact_created": False,
        "connector_binding_artifact_created": False,
        "runtime_resolver_snapshot_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "quantum_backend_artifact_created": False,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "reason_codes": list(reason_codes),
    }
    return component


def build_registry(
    *,
    repo_root: pathlib.Path,
    owner_report: dict[str, Any],
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    binding_registry: dict[str, Any],
    consumer_registry: dict[str, Any],
    agent_report: dict[str, Any],
    algorithm_report: dict[str, Any],
    binding_report: dict[str, Any],
    consumer_report: dict[str, Any],
    synthetic: bool = False,
) -> dict[str, Any]:
    metrics = collect_metrics(
        repo_root=repo_root,
        registry=None,
        owner_report=owner_report,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        consumer_registry=consumer_registry,
        agent_report=agent_report,
        algorithm_report=algorithm_report,
        binding_report=binding_report,
        consumer_report=consumer_report,
    )
    future_reason = (
        "FUTURE_COMMAND_MATRIX_PARAMETER_STACK_SCORING_ARBITRATION_REPLAY_PAPER_RUNTIME_LIVE_AND_ATOMICROWS_HASH_LAYERS_REQUIRED_BEFORE_FULL_OR_FINAL_READINESS"
    )
    components = [
        _component(
            component_id=COMPONENT_IDS[0],
            component_name="OWNER_GLOBAL_OVERRIDE_AUTHORITY",
            component_category="AUTHORITY",
            component_description="Owner authority report confirms owner override satisfies QTT internal workflow requirements while preserving evidence boundaries.",
            dependency_paths=(owner_authority.DEFAULT_POLICY,),
            dependency_reports=(OWNER_GLOBAL_OVERRIDE_REPORT,),
            expected_success_markers=(owner_authority.SUCCESS_MARKER,),
            measured_counts={
                "owner_approved_value_token_count": _int(owner_report, "owner_approved_value_token_count"),
                "owner_override_satisfied_case_count": _int(owner_report, "owner_override_satisfied_case_count"),
                "owner_override_blocked_case_count": _int(owner_report, "owner_override_blocked_case_count"),
            },
            component_present=owner_report.get("report_type") == owner_authority.REPORT_TYPE,
            component_validated=metrics["owner_global_override_authority"],
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "OWNER_GLOBAL_OVERRIDE_PRESENT",
                "OWNER_OVERRIDE_SATISFIES_INTERNAL_WORKFLOW",
                "OWNER_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[1],
            component_name="AGENT_ROLE_OPERATING_CHARTER_REGISTRY",
            component_category="AGENT_ROLE_STATIC_FOUNDATION",
            component_description="Agent role registry and report provide the 25 validated role charters consumed by algorithm bindings.",
            dependency_paths=(AGENT_CHARTER_REGISTRY,),
            dependency_reports=(AGENT_ROLE_REPORT,),
            expected_success_markers=("QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY_OK",),
            measured_counts={
                "agent_role_count_from_charter_registry": metrics["agent_role_count_from_charter_registry"],
                "agent_role_count_from_report": _int(agent_report, "agent_role_count"),
                "missing_agent_role_count": _int(agent_report, "missing_agent_role_count"),
                "agents_with_owner_override_supported_count": _int(agent_report, "agents_with_owner_override_supported_count"),
            },
            component_present=bool(agent_registry),
            component_validated=metrics["agent_role_count_from_charter_registry"] == 25
            and _int(agent_report, "agent_role_count") == 25,
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "AGENT_ROLE_CHARTER_REGISTRY_PRESENT",
                "AGENT_ROLE_COUNT_MATCHES_REPORT",
                "AGENT_ROLES_SUPPORT_OWNER_OVERRIDE_AND_QUANTUM_SCOPE",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[2],
            component_name="ALGORITHM_FORMULA_FAMILY_REGISTRY",
            component_category="ALGORITHM_STATIC_FOUNDATION",
            component_description="Algorithm registry and report provide the 15 validated formula families, including quantum-compatible families.",
            dependency_paths=(ALGORITHM_FORMULA_FAMILY_REGISTRY,),
            dependency_reports=(ALGORITHM_FORMULA_FAMILY_REPORT,),
            expected_success_markers=("QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK",),
            measured_counts={
                "algorithm_family_count_from_algorithm_registry": metrics["algorithm_family_count_from_algorithm_registry"],
                "algorithm_family_count_from_report": _int(algorithm_report, "algorithm_family_count"),
                "quantum_algorithm_family_count": metrics["quantum_algorithm_family_count"],
                "missing_algorithm_family_count": _int(algorithm_report, "missing_algorithm_family_count"),
            },
            component_present=bool(algorithm_registry),
            component_validated=metrics["algorithm_family_count_from_algorithm_registry"] == 15
            and _int(algorithm_report, "algorithm_family_count") == 15,
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "ALGORITHM_FORMULA_FAMILY_REGISTRY_PRESENT",
                "ALGORITHM_FAMILY_COUNT_MATCHES_REPORT",
                "QUANTUM_COMPATIBLE_FAMILIES_PRESERVED",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[3],
            component_name="AGENT_ALGORITHM_BINDING_REGISTRY",
            component_category="BINDING_STATIC_FOUNDATION",
            component_description="Binding registry and report prove every authorized algorithm-family role pair has one static binding.",
            dependency_paths=(AGENT_ALGORITHM_BINDING_REGISTRY,),
            dependency_reports=(AGENT_ALGORITHM_BINDING_REPORT,),
            expected_success_markers=("QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK",),
            measured_counts={
                "binding_count_from_binding_registry": metrics["binding_count_from_binding_registry"],
                "expected_binding_count_from_algorithm_registry": metrics["expected_binding_count_from_algorithm_registry"],
                "expected_binding_count_from_binding_report": metrics["expected_binding_count_from_binding_report"],
                "quantum_binding_count": metrics["quantum_binding_count"],
            },
            component_present=bool(binding_registry),
            component_validated=metrics["binding_count_from_binding_registry"]
            == metrics["expected_binding_count_from_binding_report"]
            and metrics["invalid_binding_count"] == 0,
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "AGENT_ALGORITHM_BINDING_REGISTRY_PRESENT",
                "BINDING_COUNT_MATCHES_AUTHORIZED_ROLE_PAIRS",
                "BINDINGS_REMAIN_STATIC_AND_NON_ORDERING",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[4],
            component_name="AGENT_ALGORITHM_CONSUMER_GATE",
            component_category="CONSUMER_STATIC_FOUNDATION",
            component_description="Consumer gate and report prove one allowed attempt per binding plus blocked and owner-override fail-closed cases.",
            dependency_paths=(AGENT_ALGORITHM_CONSUMER_GATE,),
            dependency_reports=(AGENT_ALGORITHM_CONSUMER_GATE_REPORT,),
            expected_success_markers=("QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK",),
            measured_counts={
                "consumer_allowed_attempt_count": metrics["consumer_allowed_attempt_count"],
                "consumer_blocked_attempt_count": metrics["consumer_blocked_attempt_count"],
                "consumer_owner_override_attempt_count": metrics["consumer_owner_override_attempt_count"],
                "quantum_consumer_allowed_attempt_count": metrics["quantum_consumer_allowed_attempt_count"],
            },
            component_present=bool(consumer_registry),
            component_validated=metrics["consumer_allowed_attempt_count"]
            == metrics["binding_count_from_binding_registry"]
            and metrics["consumer_blocked_attempt_count"] >= 5
            and metrics["consumer_owner_override_attempt_count"] >= 5,
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "AGENT_ALGORITHM_CONSUMER_GATE_PRESENT",
                "ALLOWED_ATTEMPTS_MATCH_BINDINGS",
                "BLOCKED_AND_OWNER_OVERRIDE_CASES_COVERED",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[5],
            component_name="QUANTUM_FORWARD_COMPATIBILITY",
            component_category="QUANTUM_FORWARD_STATIC_COMPATIBILITY",
            component_description="Quantum-compatible family, binding, and consumer counts remain available without claiming backend execution or advantage evidence.",
            dependency_paths=(
                MASTER_PLAN,
                ALGORITHM_FORMULA_FAMILY_REGISTRY,
                AGENT_ALGORITHM_BINDING_REGISTRY,
                AGENT_ALGORITHM_CONSUMER_GATE,
            ),
            dependency_reports=(
                ALGORITHM_FORMULA_FAMILY_REPORT,
                AGENT_ALGORITHM_BINDING_REPORT,
                AGENT_ALGORITHM_CONSUMER_GATE_REPORT,
            ),
            expected_success_markers=(
                "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK",
                "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK",
                "QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK",
            ),
            measured_counts={
                "quantum_algorithm_family_count": metrics["quantum_algorithm_family_count"],
                "quantum_binding_count": metrics["quantum_binding_count"],
                "quantum_consumer_allowed_attempt_count": metrics["quantum_consumer_allowed_attempt_count"],
                "owner_quantum_priority_supported": metrics["owner_quantum_priority_supported"],
                "owner_can_force_quantum_priority_supported": metrics["owner_can_force_quantum_priority_supported"],
            },
            component_present=True,
            component_validated=metrics["quantum_forward_design_supported"]
            and metrics["owner_quantum_priority_supported"]
            and metrics["owner_can_force_quantum_priority_supported"],
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "QUANTUM_FORWARD_DESIGN_SUPPORTED",
                "STRONGEST_CLASSICAL_COMPARATOR_AND_FALLBACK_BUNDLE_REQUIREMENTS_PRESERVED",
                "NO_QUANTUM_ADVANTAGE_OR_BACKEND_EVIDENCE_CLAIMED",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[6],
            component_name="STATIC_NO_RUNTIME_NO_EVIDENCE_BOUNDARY",
            component_category="STATIC_SCOPE_BOUNDARY",
            component_description="Cumulative readiness remains static and creates no runtime, live, order, source, connector, replay, paper, profit, or backend artifact.",
            dependency_paths=(MASTER_PLAN,),
            dependency_reports=(
                OWNER_GLOBAL_OVERRIDE_REPORT,
                AGENT_ROLE_REPORT,
                ALGORITHM_FORMULA_FAMILY_REPORT,
                AGENT_ALGORITHM_BINDING_REPORT,
                AGENT_ALGORITHM_CONSUMER_GATE_REPORT,
            ),
            expected_success_markers=(SUCCESS_MARKER,),
            measured_counts={
                "forbidden_artifact_true": metrics["forbidden_artifact_true"],
                "bundle_file_present": metrics["bundle_file_present"],
                "bundle_sha_present": metrics["bundle_sha_present"],
                "agent_algorithm_command_matrix_created": metrics["agent_algorithm_command_matrix_created"],
            },
            component_present=True,
            component_validated=metrics["authority_boundary_all_false"],
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "STATIC_ONLY_BOUNDARY_CONFIRMED",
                "NO_RUNTIME_OR_LIVE_ARTIFACT_CREATED",
                "NO_SOURCE_CONNECTOR_REPLAY_PAPER_PROFIT_OR_BACKEND_EVIDENCE_CREATED",
            ),
        ),
        _component(
            component_id=COMPONENT_IDS[7],
            component_name="FUTURE_PR_DEPENDENCY_BOUNDARY",
            component_category="FUTURE_LAYER_BOUNDARY",
            component_description="Full and final readiness remain false until later command matrix, parameter-stack, scoring, arbitration, replay, paper, runtime, live, and bundle/hash layers exist.",
            dependency_paths=(MASTER_PLAN,),
            dependency_reports=(
                AGENT_ALGORITHM_BINDING_REPORT,
                AGENT_ALGORITHM_CONSUMER_GATE_REPORT,
            ),
            expected_success_markers=(SUCCESS_MARKER,),
            measured_counts={
                "future_command_matrix_required": True,
                "future_parameter_stack_layers_required": True,
                "future_scoring_ranking_layers_required": True,
                "future_quantum_classical_arbitration_required": True,
                "future_replay_paper_evidence_required": True,
                "future_runtime_live_readiness_required": True,
                "future_atomicrows_bundle_hash_required": True,
            },
            component_present=True,
            component_validated=True,
            static_foundation_contribution=True,
            qtt_internal_ready_contribution=True,
            normal_static_ready_contribution=True,
            normal_full_ready_contribution=False,
            final_ready_contribution=False,
            quantum_forward_contribution=True,
            future_pr_dependency_reason=future_reason,
            reason_codes=(
                "NORMAL_FULL_READINESS_REMAINS_FALSE",
                "FINAL_READY_REMAINS_FALSE",
                "FUTURE_SELECTION_SCORING_ARBITRATION_AND_LIVE_LAYERS_REQUIRED",
            ),
        ),
    ]
    registry = {
        "registry_type": REGISTRY_TYPE,
        "registry_version": REGISTRY_VERSION,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_readiness_substance": MASTER_PLAN.as_posix(),
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "agent_algorithm_binding_registry_dependency": (
            AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        ),
        "agent_algorithm_consumer_gate_dependency": (
            AGENT_ALGORITHM_CONSUMER_GATE.as_posix()
        ),
        "owner_global_override_report_dependency": OWNER_GLOBAL_OVERRIDE_REPORT.as_posix(),
        "agent_role_report_dependency": AGENT_ROLE_REPORT.as_posix(),
        "algorithm_formula_family_report_dependency": (
            ALGORITHM_FORMULA_FAMILY_REPORT.as_posix()
        ),
        "agent_algorithm_binding_report_dependency": (
            AGENT_ALGORITHM_BINDING_REPORT.as_posix()
        ),
        "agent_algorithm_consumer_gate_report_dependency": (
            AGENT_ALGORITHM_CONSUMER_GATE_REPORT.as_posix()
        ),
        "readiness_generation_policy": READINESS_GENERATION_POLICY,
        "master_plan_followed_as_controlling_doctrine": True,
        "owner_global_override_authority": metrics["owner_global_override_authority"],
        "owner_override_satisfies_all_qtt_internal_requirements": metrics[
            "owner_override_satisfies_all_qtt_internal_requirements"
        ],
        "owner_override_satisfies_agent_algorithm_readiness": metrics[
            "owner_override_satisfies_agent_algorithm_readiness"
        ],
        "static_agent_algorithm_foundation_ready": metrics[
            "static_agent_algorithm_foundation_ready"
        ],
        "normal_static_agent_algorithm_coverage_ready": metrics[
            "normal_static_agent_algorithm_coverage_ready"
        ],
        "normal_full_agent_algorithm_coverage_ready": False,
        "qtt_internal_agent_algorithm_ready": metrics[
            "qtt_internal_agent_algorithm_ready"
        ],
        "future_command_matrix_required": True,
        "agent_algorithm_command_matrix_created": False,
        "future_parameter_stack_layers_required": True,
        "future_scoring_ranking_layers_required": True,
        "future_quantum_classical_arbitration_required": True,
        "future_replay_paper_evidence_required": True,
        "future_runtime_live_readiness_required": True,
        "future_atomicrows_bundle_hash_required": True,
        "chatgpt_authority_over_owner": False,
        "codex_authority_over_owner": False,
        "qtt_agent_authority_over_owner": False,
        "quantum_forward_design_supported": metrics["quantum_forward_design_supported"],
        "quantum_evidence_claim_created": False,
        "alpha_evidence_claim_created": False,
        "profit_evidence_claim_created": False,
        "latency_superiority_evidence_claim_created": False,
        "execution_superiority_evidence_claim_created": False,
        "static_agent_algorithm_cumulative_readiness_gate_created": True,
        "runtime_artifact_created": False,
        "live_artifact_created": False,
        "order_artifact_created": False,
        "source_acceptance_artifact_created": False,
        "connector_binding_artifact_created": False,
        "runtime_resolver_snapshot_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "quantum_backend_artifact_created": False,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "uses_pr_number_as_authority": False,
        "final_ready": False,
        "readiness_components": components,
    }
    if synthetic:
        registry.update(
            {
                "fixture_id": (
                    "SYNTHETIC_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FIXTURE"
                ),
                "fixture_version": (
                    "SYNTHETIC_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FIXTURE_V1"
                ),
                "fixture_authority_class": (
                    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_BINDING_READINESS_AUTHORITY"
                ),
                "mode": "SOURCE_REQUIRED",
                "execution": "DISABLED",
            }
        )
    return registry


def build_report(
    registry: dict[str, Any],
    *,
    repo_root: pathlib.Path,
    owner_report: dict[str, Any],
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    binding_registry: dict[str, Any],
    consumer_registry: dict[str, Any],
    agent_report: dict[str, Any],
    algorithm_report: dict[str, Any],
    binding_report: dict[str, Any],
    consumer_report: dict[str, Any],
) -> dict[str, Any]:
    metrics = collect_metrics(
        repo_root=repo_root,
        registry=registry,
        owner_report=owner_report,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        consumer_registry=consumer_registry,
        agent_report=agent_report,
        algorithm_report=algorithm_report,
        binding_report=binding_report,
        consumer_report=consumer_report,
    )
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_readiness_substance": MASTER_PLAN.as_posix(),
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "agent_algorithm_binding_registry_dependency": (
            AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        ),
        "agent_algorithm_consumer_gate_dependency": (
            AGENT_ALGORITHM_CONSUMER_GATE.as_posix()
        ),
        "owner_global_override_report_dependency": OWNER_GLOBAL_OVERRIDE_REPORT.as_posix(),
        "agent_role_report_dependency": AGENT_ROLE_REPORT.as_posix(),
        "algorithm_formula_family_report_dependency": (
            ALGORITHM_FORMULA_FAMILY_REPORT.as_posix()
        ),
        "agent_algorithm_binding_report_dependency": (
            AGENT_ALGORITHM_BINDING_REPORT.as_posix()
        ),
        "agent_algorithm_consumer_gate_report_dependency": (
            AGENT_ALGORITHM_CONSUMER_GATE_REPORT.as_posix()
        ),
        "readiness_generation_policy": READINESS_GENERATION_POLICY,
        "master_plan_followed_as_controlling_doctrine": registry.get(
            "master_plan_followed_as_controlling_doctrine"
        )
        is True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "component_count": metrics["component_count"],
        "required_component_count": metrics["required_component_count"],
        "components_present_count": metrics["components_present_count"],
        "missing_component_count": metrics["missing_component_count"],
        "invalid_component_order_count": metrics["invalid_component_order_count"],
        "agent_role_count_from_charter_registry": metrics[
            "agent_role_count_from_charter_registry"
        ],
        "algorithm_family_count_from_algorithm_registry": metrics[
            "algorithm_family_count_from_algorithm_registry"
        ],
        "binding_count_from_binding_registry": metrics["binding_count_from_binding_registry"],
        "expected_binding_count_from_binding_report": metrics[
            "expected_binding_count_from_binding_report"
        ],
        "consumer_allowed_attempt_count": metrics["consumer_allowed_attempt_count"],
        "consumer_blocked_attempt_count": metrics["consumer_blocked_attempt_count"],
        "consumer_owner_override_attempt_count": metrics[
            "consumer_owner_override_attempt_count"
        ],
        "invalid_agent_role_count": metrics["invalid_agent_role_count"],
        "invalid_algorithm_family_count": metrics["invalid_algorithm_family_count"],
        "invalid_binding_count": metrics["invalid_binding_count"],
        "invalid_consumer_authorization_count": metrics[
            "invalid_consumer_authorization_count"
        ],
        "owner_global_override_authority": registry.get("owner_global_override_authority")
        is True,
        "owner_override_satisfies_all_qtt_internal_requirements": registry.get(
            "owner_override_satisfies_all_qtt_internal_requirements"
        )
        is True,
        "owner_override_satisfies_agent_algorithm_readiness": registry.get(
            "owner_override_satisfies_agent_algorithm_readiness"
        )
        is True,
        "static_agent_algorithm_foundation_ready": registry.get(
            "static_agent_algorithm_foundation_ready"
        )
        is True,
        "normal_static_agent_algorithm_coverage_ready": registry.get(
            "normal_static_agent_algorithm_coverage_ready"
        )
        is True,
        "normal_full_agent_algorithm_coverage_ready": registry.get(
            "normal_full_agent_algorithm_coverage_ready"
        )
        is True,
        "qtt_internal_agent_algorithm_ready": registry.get(
            "qtt_internal_agent_algorithm_ready"
        )
        is True,
        "future_command_matrix_required": registry.get("future_command_matrix_required")
        is True,
        "agent_algorithm_command_matrix_created": registry.get(
            "agent_algorithm_command_matrix_created"
        )
        is True
        or metrics["agent_algorithm_command_matrix_created"],
        "future_parameter_stack_layers_required": registry.get(
            "future_parameter_stack_layers_required"
        )
        is True,
        "future_scoring_ranking_layers_required": registry.get(
            "future_scoring_ranking_layers_required"
        )
        is True,
        "future_quantum_classical_arbitration_required": registry.get(
            "future_quantum_classical_arbitration_required"
        )
        is True,
        "future_replay_paper_evidence_required": registry.get(
            "future_replay_paper_evidence_required"
        )
        is True,
        "future_runtime_live_readiness_required": registry.get(
            "future_runtime_live_readiness_required"
        )
        is True,
        "future_atomicrows_bundle_hash_required": registry.get(
            "future_atomicrows_bundle_hash_required"
        )
        is True,
        "quantum_forward_design_supported": registry.get(
            "quantum_forward_design_supported"
        )
        is True,
        "quantum_algorithm_family_count": metrics["quantum_algorithm_family_count"],
        "quantum_binding_count": metrics["quantum_binding_count"],
        "quantum_consumer_allowed_attempt_count": metrics[
            "quantum_consumer_allowed_attempt_count"
        ],
        "owner_quantum_priority_supported": metrics["owner_quantum_priority_supported"],
        "owner_can_force_quantum_priority_supported": metrics[
            "owner_can_force_quantum_priority_supported"
        ],
        "alpha_evidence_claim_created": registry.get("alpha_evidence_claim_created")
        is True,
        "profit_evidence_claim_created": registry.get("profit_evidence_claim_created")
        is True,
        "latency_superiority_evidence_claim_created": registry.get(
            "latency_superiority_evidence_claim_created"
        )
        is True,
        "execution_superiority_evidence_claim_created": registry.get(
            "execution_superiority_evidence_claim_created"
        )
        is True,
        "quantum_evidence_claim_created": registry.get("quantum_evidence_claim_created")
        is True,
        "static_agent_algorithm_cumulative_readiness_gate_created": registry.get(
            "static_agent_algorithm_cumulative_readiness_gate_created"
        )
        is True,
        "runtime_artifact_created": registry.get("runtime_artifact_created") is True,
        "live_artifact_created": registry.get("live_artifact_created") is True,
        "order_artifact_created": registry.get("order_artifact_created") is True,
        "source_acceptance_artifact_created": registry.get(
            "source_acceptance_artifact_created"
        )
        is True,
        "connector_binding_artifact_created": registry.get(
            "connector_binding_artifact_created"
        )
        is True,
        "runtime_resolver_snapshot_created": registry.get(
            "runtime_resolver_snapshot_created"
        )
        is True,
        "replay_execution_created": registry.get("replay_execution_created") is True,
        "paper_execution_created": registry.get("paper_execution_created") is True,
        "quantum_backend_artifact_created": registry.get(
            "quantum_backend_artifact_created"
        )
        is True,
        "bundle_file_present": metrics["bundle_file_present"],
        "bundle_sha_present": metrics["bundle_sha_present"],
        "uses_pr_number_as_authority": registry.get("uses_pr_number_as_authority")
        is True
        or binding_gate._uses_pr_number_as_authority_values(registry),
        "final_ready": registry.get("final_ready") is True,
        "authority_boundary_all_false": metrics["authority_boundary_all_false"]
        and not _has_forbidden_true(registry),
    }
    return report


def build_schema() -> dict[str, Any]:
    false_bool = {"const": False}
    true_bool = {"const": True}
    string_array = {"type": "array", "minItems": 1, "items": {"type": "string"}}
    component_properties: dict[str, Any] = {
        "component_id": {"enum": list(COMPONENT_IDS)},
        "component_name": {"type": "string"},
        "component_category": {"type": "string"},
        "component_description": {"type": "string"},
        "dependency_paths": string_array,
        "dependency_reports": string_array,
        "expected_success_markers": string_array,
        "measured_counts": {"type": "object"},
        "component_present": {"type": "boolean"},
        "component_validated": {"type": "boolean"},
        "static_foundation_contribution": {"type": "boolean"},
        "owner_override_supported": true_bool,
        "owner_override_satisfaction_basis": {"const": OWNER_OVERRIDE_SATISFACTION_BASIS},
        "qtt_internal_ready_contribution": {"type": "boolean"},
        "normal_static_ready_contribution": {"type": "boolean"},
        "normal_full_ready_contribution": {"type": "boolean"},
        "final_ready_contribution": false_bool,
        "quantum_forward_contribution": {"type": "boolean"},
        "future_pr_dependency_reason": {"type": "string"},
        "reason_codes": string_array,
    }
    for field in FALSE_ARTIFACT_AND_EVIDENCE_FIELDS:
        component_properties[field] = false_bool
    component_properties["bundle_file_present"] = false_bool
    component_properties["bundle_sha_present"] = false_bool

    properties: dict[str, Any] = {
        "registry_type": {"const": REGISTRY_TYPE},
        "registry_version": {"const": REGISTRY_VERSION},
        "deterministic_output": true_bool,
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "source_of_readiness_substance": {"const": MASTER_PLAN.as_posix()},
        "agent_charter_registry_dependency": {"const": AGENT_CHARTER_REGISTRY.as_posix()},
        "algorithm_formula_family_registry_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        },
        "agent_algorithm_binding_registry_dependency": {
            "const": AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        },
        "agent_algorithm_consumer_gate_dependency": {
            "const": AGENT_ALGORITHM_CONSUMER_GATE.as_posix()
        },
        "owner_global_override_report_dependency": {
            "const": OWNER_GLOBAL_OVERRIDE_REPORT.as_posix()
        },
        "agent_role_report_dependency": {"const": AGENT_ROLE_REPORT.as_posix()},
        "algorithm_formula_family_report_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REPORT.as_posix()
        },
        "agent_algorithm_binding_report_dependency": {
            "const": AGENT_ALGORITHM_BINDING_REPORT.as_posix()
        },
        "agent_algorithm_consumer_gate_report_dependency": {
            "const": AGENT_ALGORITHM_CONSUMER_GATE_REPORT.as_posix()
        },
        "readiness_generation_policy": {"const": READINESS_GENERATION_POLICY},
        "master_plan_followed_as_controlling_doctrine": true_bool,
        "owner_global_override_authority": true_bool,
        "owner_override_satisfies_all_qtt_internal_requirements": true_bool,
        "owner_override_satisfies_agent_algorithm_readiness": true_bool,
        "static_agent_algorithm_foundation_ready": true_bool,
        "normal_static_agent_algorithm_coverage_ready": true_bool,
        "normal_full_agent_algorithm_coverage_ready": false_bool,
        "qtt_internal_agent_algorithm_ready": true_bool,
        "future_command_matrix_required": true_bool,
        "future_parameter_stack_layers_required": true_bool,
        "future_scoring_ranking_layers_required": true_bool,
        "future_quantum_classical_arbitration_required": true_bool,
        "future_replay_paper_evidence_required": true_bool,
        "future_runtime_live_readiness_required": true_bool,
        "future_atomicrows_bundle_hash_required": true_bool,
        "quantum_forward_design_supported": true_bool,
        "static_agent_algorithm_cumulative_readiness_gate_created": true_bool,
        "readiness_components": {
            "type": "array",
            "minItems": len(COMPONENT_IDS),
            "maxItems": len(COMPONENT_IDS),
            "uniqueItems": True,
            "items": {"$ref": "#/$defs/readiness_component"},
        },
        "fixture_id": {"type": "string"},
        "fixture_version": {"type": "string"},
        "fixture_authority_class": {"type": "string"},
        "mode": {"const": "SOURCE_REQUIRED"},
        "execution": {"const": "DISABLED"},
    }
    for field in TOP_FALSE_FIELDS:
        properties[field] = false_bool

    report_properties: dict[str, Any] = {
        "report_type": {"const": REPORT_TYPE},
        "deterministic_output": true_bool,
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "source_of_readiness_substance": {"const": MASTER_PLAN.as_posix()},
        "agent_charter_registry_dependency": {"const": AGENT_CHARTER_REGISTRY.as_posix()},
        "algorithm_formula_family_registry_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        },
        "agent_algorithm_binding_registry_dependency": {
            "const": AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        },
        "agent_algorithm_consumer_gate_dependency": {
            "const": AGENT_ALGORITHM_CONSUMER_GATE.as_posix()
        },
        "owner_global_override_report_dependency": {
            "const": OWNER_GLOBAL_OVERRIDE_REPORT.as_posix()
        },
        "agent_role_report_dependency": {"const": AGENT_ROLE_REPORT.as_posix()},
        "algorithm_formula_family_report_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REPORT.as_posix()
        },
        "agent_algorithm_binding_report_dependency": {
            "const": AGENT_ALGORITHM_BINDING_REPORT.as_posix()
        },
        "agent_algorithm_consumer_gate_report_dependency": {
            "const": AGENT_ALGORITHM_CONSUMER_GATE_REPORT.as_posix()
        },
        "readiness_generation_policy": {"const": READINESS_GENERATION_POLICY},
        "master_plan_followed_as_controlling_doctrine": true_bool,
        "architecture_emphasis": {"const": ARCHITECTURE_EMPHASIS},
        "component_count": {"type": "integer"},
        "required_component_count": {"const": len(COMPONENT_IDS)},
        "components_present_count": {"type": "integer"},
        "missing_component_count": {"type": "integer"},
        "invalid_component_order_count": {"type": "integer"},
        "agent_role_count_from_charter_registry": {"type": "integer"},
        "algorithm_family_count_from_algorithm_registry": {"type": "integer"},
        "binding_count_from_binding_registry": {"type": "integer"},
        "expected_binding_count_from_binding_report": {"type": "integer"},
        "consumer_allowed_attempt_count": {"type": "integer"},
        "consumer_blocked_attempt_count": {"type": "integer"},
        "consumer_owner_override_attempt_count": {"type": "integer"},
        "invalid_agent_role_count": {"type": "integer"},
        "invalid_algorithm_family_count": {"type": "integer"},
        "invalid_binding_count": {"type": "integer"},
        "invalid_consumer_authorization_count": {"type": "integer"},
        "owner_global_override_authority": true_bool,
        "owner_override_satisfies_all_qtt_internal_requirements": true_bool,
        "owner_override_satisfies_agent_algorithm_readiness": true_bool,
        "static_agent_algorithm_foundation_ready": true_bool,
        "normal_static_agent_algorithm_coverage_ready": true_bool,
        "normal_full_agent_algorithm_coverage_ready": false_bool,
        "qtt_internal_agent_algorithm_ready": true_bool,
        "future_command_matrix_required": true_bool,
        "agent_algorithm_command_matrix_created": false_bool,
        "future_parameter_stack_layers_required": true_bool,
        "future_scoring_ranking_layers_required": true_bool,
        "future_quantum_classical_arbitration_required": true_bool,
        "future_replay_paper_evidence_required": true_bool,
        "future_runtime_live_readiness_required": true_bool,
        "future_atomicrows_bundle_hash_required": true_bool,
        "quantum_forward_design_supported": true_bool,
        "quantum_algorithm_family_count": {"type": "integer"},
        "quantum_binding_count": {"type": "integer"},
        "quantum_consumer_allowed_attempt_count": {"type": "integer"},
        "owner_quantum_priority_supported": true_bool,
        "owner_can_force_quantum_priority_supported": true_bool,
        "static_agent_algorithm_cumulative_readiness_gate_created": true_bool,
        "authority_boundary_all_false": true_bool,
    }
    for field in (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    ):
        report_properties[field] = false_bool

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {
            "readiness_component": {
                "type": "object",
                "additionalProperties": False,
                "properties": component_properties,
                "required": list(COMPONENT_FIELDS),
            },
            "agent_algorithm_cumulative_readiness_gate_report": {
                "type": "object",
                "additionalProperties": False,
                "properties": report_properties,
                "required": list(REPORT_FIELDS),
            },
        },
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(TOP_FIELDS),
    }


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_FIELDS):
        failures.append("schema.required must match cumulative readiness top fields")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return [*failures, "schema.$defs must be an object"]
    component_schema = defs.get("readiness_component")
    if not isinstance(component_schema, dict):
        failures.append("schema readiness_component definition is missing")
    elif component_schema.get("required") != list(COMPONENT_FIELDS):
        failures.append("schema readiness_component.required is invalid")
    report_schema = defs.get("agent_algorithm_cumulative_readiness_gate_report")
    if not isinstance(report_schema, dict):
        failures.append("schema report definition is missing")
    elif report_schema.get("required") != list(REPORT_FIELDS):
        failures.append("schema report.required is invalid")
    return failures


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    missing = sorted(expected_fields - set(value))
    unexpected = sorted(set(value) - expected_fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _validate_top_level(
    value: dict[str, Any],
    *,
    label: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(
        value,
        set(TOP_FIELDS if label == "registry" else (*TOP_FIELDS, *FIXTURE_EXTRA_FIELDS)),
        label,
    )
    if schema is not None:
        failures.extend(validate_json_schema_subset(value, schema, root_schema=schema))
    if label == "fixture":
        if value.get("fixture_id") != (
            "SYNTHETIC_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FIXTURE"
        ):
            failures.append("fixture.fixture_id is invalid")
        if value.get("fixture_authority_class") != (
            "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_BINDING_READINESS_AUTHORITY"
        ):
            failures.append("fixture.fixture_authority_class is invalid")
    for field in TOP_TRUE_FIELDS:
        if value.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    if value.get("normal_full_agent_algorithm_coverage_ready") is not False:
        failures.append(f"{label}.normal_full_agent_algorithm_coverage_ready must be false")
    for field in TOP_FALSE_FIELDS:
        if value.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if value.get("readiness_generation_policy") != READINESS_GENERATION_POLICY:
        failures.append(f"{label}.readiness_generation_policy is invalid")
    if binding_gate._uses_pr_number_as_authority_values(value):
        failures.append(f"{label} must not use a delivery label as authority")
    return failures


def _validate_components(value: dict[str, Any], *, label: str) -> list[str]:
    failures: list[str] = []
    components = _items(value, "readiness_components")
    if len(components) != len(COMPONENT_IDS):
        failures.append(f"{label}.readiness_components must contain exactly 8 components")
    component_ids = [component.get("component_id") for component in components]
    if component_ids != list(COMPONENT_IDS):
        failures.append(f"{label}.readiness_components must use deterministic order")
    if len(set(component_ids)) != len(component_ids):
        failures.append(f"{label}.readiness_components component_id values must be unique")
    for index, component in enumerate(components):
        prefix = f"{label}.readiness_components[{index}]"
        failures.extend(_require_exact_fields(component, set(COMPONENT_FIELDS), prefix))
        for array_field in (
            "dependency_paths",
            "dependency_reports",
            "expected_success_markers",
            "reason_codes",
        ):
            items = component.get(array_field)
            if not isinstance(items, list) or not items:
                failures.append(f"{prefix}.{array_field} must be a non-empty array")
        measured_counts = component.get("measured_counts")
        if not isinstance(measured_counts, dict) or not measured_counts:
            failures.append(f"{prefix}.measured_counts must be a non-empty object")
        for field in FALSE_ARTIFACT_AND_EVIDENCE_FIELDS:
            if field in component and component.get(field) is not False:
                failures.append(f"{prefix}.{field} must be false")
        for field in ("bundle_file_present", "bundle_sha_present"):
            if component.get(field) is not False:
                failures.append(f"{prefix}.{field} must be false")
        if component.get("owner_override_supported") is not True:
            failures.append(f"{prefix}.owner_override_supported must be true")
        if component.get("owner_override_satisfaction_basis") != OWNER_OVERRIDE_SATISFACTION_BASIS:
            failures.append(f"{prefix}.owner_override_satisfaction_basis is invalid")
        if index <= 4 and component.get("static_foundation_contribution") is not True:
            failures.append(f"{prefix} must contribute to static foundation readiness")
        if index == 5 and component.get("quantum_forward_contribution") is not True:
            failures.append(f"{prefix} must preserve quantum-forward compatibility")
        if index == 6 and component.get("component_validated") is not True:
            failures.append(f"{prefix} must validate the no-runtime/no-evidence boundary")
        if index == 7:
            if component.get("normal_full_ready_contribution") is not False:
                failures.append(f"{prefix}.normal_full_ready_contribution must be false")
            if component.get("final_ready_contribution") is not False:
                failures.append(f"{prefix}.final_ready_contribution must be false")
    return failures


def _validate_dependency_consistency(
    *,
    metrics: dict[str, Any],
    owner_report: dict[str, Any] | None,
    agent_report: dict[str, Any] | None,
    algorithm_report: dict[str, Any] | None,
    binding_report: dict[str, Any] | None,
    consumer_report: dict[str, Any] | None,
) -> list[str]:
    failures: list[str] = []
    if not metrics["owner_global_override_authority"]:
        failures.append("owner global override support is missing or blocked")
    if metrics["agent_role_count_from_charter_registry"] != 25:
        failures.append("agent role registry count must be 25")
    if _int(agent_report, "agent_role_count") != metrics["agent_role_count_from_charter_registry"]:
        failures.append("agent role registry/report counts conflict")
    if metrics["algorithm_family_count_from_algorithm_registry"] != 15:
        failures.append("algorithm family registry count must be 15")
    if _int(algorithm_report, "algorithm_family_count") != metrics[
        "algorithm_family_count_from_algorithm_registry"
    ]:
        failures.append("algorithm registry/report counts conflict")
    if metrics["binding_count_from_binding_registry"] != metrics[
        "expected_binding_count_from_algorithm_registry"
    ]:
        failures.append("binding count must equal expected count from algorithm authorized roles")
    if metrics["binding_count_from_binding_registry"] != metrics[
        "expected_binding_count_from_binding_report"
    ]:
        failures.append("binding registry/report counts conflict")
    if _int(binding_report, "actual_binding_count") != metrics[
        "binding_count_from_binding_registry"
    ]:
        failures.append("binding report actual count conflicts with registry")
    if metrics["consumer_allowed_attempt_count"] != metrics[
        "binding_count_from_binding_registry"
    ]:
        failures.append("consumer allowed attempt count must equal binding count")
    if _int(consumer_report, "actual_allowed_attempt_count") != metrics[
        "consumer_allowed_attempt_count"
    ]:
        failures.append("consumer gate registry/report allowed counts conflict")
    if metrics["consumer_blocked_attempt_count"] < 5:
        failures.append("consumer blocked attempt count must be at least 5")
    if metrics["consumer_owner_override_attempt_count"] < 5:
        failures.append("consumer owner override attempt count must be at least 5")
    for field in (
        "invalid_agent_role_count",
        "invalid_algorithm_family_count",
        "invalid_binding_count",
        "invalid_consumer_authorization_count",
    ):
        if metrics[field] != 0:
            failures.append(f"{field} must be 0")
    if metrics["upstream_final_ready_true"]:
        failures.append("upstream final_ready must not be true")
    if metrics["forbidden_artifact_true"]:
        failures.append("upstream artifacts or evidence claims must remain false")
    if not metrics["static_agent_algorithm_foundation_ready"]:
        failures.append("static agent-algorithm foundation cannot be proven")
    if not metrics["quantum_forward_design_supported"]:
        failures.append("quantum-forward design support cannot be proven")
    if not metrics["owner_quantum_priority_supported"]:
        failures.append("owner quantum priority support cannot be proven")
    if not metrics["owner_can_force_quantum_priority_supported"]:
        failures.append("owner-forced quantum priority support cannot be proven")
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("agent_algorithm_cumulative_readiness_gate_report")
    if not isinstance(report_schema, dict):
        return ["schema report definition is missing"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    exact_counts = {
        "component_count": 8,
        "required_component_count": 8,
        "components_present_count": 8,
        "missing_component_count": 0,
        "invalid_component_order_count": 0,
        "agent_role_count_from_charter_registry": 25,
        "algorithm_family_count_from_algorithm_registry": 15,
        "invalid_agent_role_count": 0,
        "invalid_algorithm_family_count": 0,
        "invalid_binding_count": 0,
        "invalid_consumer_authorization_count": 0,
    }
    for field, expected in exact_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    if report.get("binding_count_from_binding_registry") != report.get(
        "expected_binding_count_from_binding_report"
    ):
        failures.append("report binding count must equal expected binding count")
    if report.get("consumer_allowed_attempt_count") != report.get(
        "binding_count_from_binding_registry"
    ):
        failures.append("report consumer allowed attempt count must equal binding count")
    for field, minimum in (
        ("consumer_blocked_attempt_count", 5),
        ("consumer_owner_override_attempt_count", 5),
        ("quantum_algorithm_family_count", 9),
        ("quantum_binding_count", 1),
        ("quantum_consumer_allowed_attempt_count", 1),
    ):
        if report.get(field, 0) < minimum:
            failures.append(f"report.{field} must be at least {minimum}")
    for field in (
        "deterministic_output",
        "master_plan_followed_as_controlling_doctrine",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "owner_override_satisfies_agent_algorithm_readiness",
        "static_agent_algorithm_foundation_ready",
        "normal_static_agent_algorithm_coverage_ready",
        "qtt_internal_agent_algorithm_ready",
        "future_command_matrix_required",
        "future_parameter_stack_layers_required",
        "future_scoring_ranking_layers_required",
        "future_quantum_classical_arbitration_required",
        "future_replay_paper_evidence_required",
        "future_runtime_live_readiness_required",
        "future_atomicrows_bundle_hash_required",
        "quantum_forward_design_supported",
        "owner_quantum_priority_supported",
        "owner_can_force_quantum_priority_supported",
        "static_agent_algorithm_cumulative_readiness_gate_created",
        "authority_boundary_all_false",
    ):
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    for field in (
        "normal_full_agent_algorithm_coverage_ready",
        "agent_algorithm_command_matrix_created",
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    ):
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must use deterministic sentinel")
    if report.get("architecture_emphasis") != ARCHITECTURE_EMPHASIS:
        failures.append("report.architecture_emphasis is invalid")
    if report != json.loads(serialize_json(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
    owner_report_path: pathlib.Path,
    agent_registry_path: pathlib.Path,
    algorithm_registry_path: pathlib.Path,
    binding_registry_path: pathlib.Path,
    consumer_registry_path: pathlib.Path,
    agent_report_path: pathlib.Path,
    algorithm_report_path: pathlib.Path,
    binding_report_path: pathlib.Path,
    consumer_report_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    registry, registry_failures = _load_registry(root / registry_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    owner_report, owner_report_failures = _load_json(root / owner_report_path)
    agent_registry, agent_registry_failures = _load_registry(root / agent_registry_path)
    algorithm_registry, algorithm_registry_failures = _load_registry(
        root / algorithm_registry_path
    )
    binding_registry, binding_registry_failures = _load_registry(
        root / binding_registry_path
    )
    consumer_registry, consumer_registry_failures = _load_registry(
        root / consumer_registry_path
    )
    agent_report, agent_report_failures = _load_json(root / agent_report_path)
    algorithm_report, algorithm_report_failures = _load_json(root / algorithm_report_path)
    binding_report, binding_report_failures = _load_json(root / binding_report_path)
    consumer_report, consumer_report_failures = _load_json(root / consumer_report_path)

    for current_failures in (
        schema_failures,
        registry_failures,
        fixture_failures,
        owner_report_failures,
        agent_registry_failures,
        algorithm_registry_failures,
        binding_registry_failures,
        consumer_registry_failures,
        agent_report_failures,
        algorithm_report_failures,
        binding_report_failures,
        consumer_report_failures,
    ):
        failures.extend(current_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if registry is not None:
        failures.extend(_validate_top_level(registry, label="registry", schema=schema))
        failures.extend(_validate_components(registry, label="registry"))
    if fixture is not None:
        failures.extend(_validate_top_level(fixture, label="fixture", schema=schema))
        failures.extend(_validate_components(fixture, label="fixture"))

    metrics = collect_metrics(
        repo_root=root,
        registry=registry or {},
        owner_report=owner_report or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        binding_registry=binding_registry or {},
        consumer_registry=consumer_registry or {},
        agent_report=agent_report or {},
        algorithm_report=algorithm_report or {},
        binding_report=binding_report or {},
        consumer_report=consumer_report or {},
    )
    failures.extend(
        _validate_dependency_consistency(
            metrics=metrics,
            owner_report=owner_report,
            agent_report=agent_report,
            algorithm_report=algorithm_report,
            binding_report=binding_report,
            consumer_report=consumer_report,
        )
    )
    if metrics["agent_algorithm_command_matrix_created"]:
        failures.append("agent-algorithm command matrix must not be created")
    if metrics["bundle_file_present"]:
        failures.append("AtomicRows.bundle.jsonl must be absent")
    if metrics["bundle_sha_present"]:
        failures.append("AtomicRows.bundle.sha256 must be absent")
    failures.extend(binding_gate._master_plan_has_no_diff(root))

    report = build_report(
        registry or {},
        repo_root=root,
        owner_report=owner_report or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        binding_registry=binding_registry or {},
        consumer_registry=consumer_registry or {},
        agent_report=agent_report or {},
        algorithm_report=algorithm_report or {},
        binding_report=binding_report or {},
        consumer_report=consumer_report or {},
    )
    second_report = build_report(
        registry or {},
        repo_root=root,
        owner_report=owner_report or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        binding_registry=binding_registry or {},
        consumer_registry=consumer_registry or {},
        agent_report=agent_report or {},
        algorithm_report=algorithm_report or {},
        binding_report=binding_report or {},
        consumer_report=consumer_report or {},
    )
    if report != second_report:
        failures.append("generated cumulative readiness report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: cumulative agent-algorithm readiness is static "
            "internal readiness, not final production readiness"
        )

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    owner_report = json.loads((root / OWNER_GLOBAL_OVERRIDE_REPORT).read_text(encoding="utf-8"))
    agent_registry = load_registry(root / AGENT_CHARTER_REGISTRY)
    algorithm_registry = load_registry(root / ALGORITHM_FORMULA_FAMILY_REGISTRY)
    binding_registry = load_registry(root / AGENT_ALGORITHM_BINDING_REGISTRY)
    consumer_registry = load_registry(root / AGENT_ALGORITHM_CONSUMER_GATE)
    agent_report = json.loads((root / AGENT_ROLE_REPORT).read_text(encoding="utf-8"))
    algorithm_report = json.loads(
        (root / ALGORITHM_FORMULA_FAMILY_REPORT).read_text(encoding="utf-8")
    )
    binding_report = json.loads((root / AGENT_ALGORITHM_BINDING_REPORT).read_text(encoding="utf-8"))
    consumer_report = json.loads(
        (root / AGENT_ALGORITHM_CONSUMER_GATE_REPORT).read_text(encoding="utf-8")
    )
    schema = build_schema()
    registry = build_registry(
        repo_root=root,
        owner_report=owner_report,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        consumer_registry=consumer_registry,
        agent_report=agent_report,
        algorithm_report=algorithm_report,
        binding_report=binding_report,
        consumer_report=consumer_report,
        synthetic=False,
    )
    fixture = build_registry(
        repo_root=root,
        owner_report=owner_report,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        consumer_registry=consumer_registry,
        agent_report=agent_report,
        algorithm_report=algorithm_report,
        binding_report=binding_report,
        consumer_report=consumer_report,
        synthetic=True,
    )
    report = build_report(
        registry,
        repo_root=root,
        owner_report=owner_report,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        consumer_registry=consumer_registry,
        agent_report=agent_report,
        algorithm_report=algorithm_report,
        binding_report=binding_report,
        consumer_report=consumer_report,
    )
    write_json(root / DEFAULT_SCHEMA, schema)
    write_json(root / DEFAULT_REGISTRY, registry)
    write_json(root / DEFAULT_FIXTURE, fixture)
    write_json(root / DEFAULT_REPORT, report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "final"], default="dev")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--owner-report", default=str(OWNER_GLOBAL_OVERRIDE_REPORT))
    parser.add_argument("--agent-registry", default=str(AGENT_CHARTER_REGISTRY))
    parser.add_argument(
        "--algorithm-registry",
        default=str(ALGORITHM_FORMULA_FAMILY_REGISTRY),
    )
    parser.add_argument(
        "--binding-registry",
        default=str(AGENT_ALGORITHM_BINDING_REGISTRY),
    )
    parser.add_argument(
        "--consumer-registry",
        default=str(AGENT_ALGORITHM_CONSUMER_GATE),
    )
    parser.add_argument("--agent-report", default=str(AGENT_ROLE_REPORT))
    parser.add_argument(
        "--algorithm-report",
        default=str(ALGORITHM_FORMULA_FAMILY_REPORT),
    )
    parser.add_argument("--binding-report", default=str(AGENT_ALGORITHM_BINDING_REPORT))
    parser.add_argument("--consumer-report", default=str(AGENT_ALGORITHM_CONSUMER_GATE_REPORT))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--write-static-artifacts", action="store_true")
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    if args.write_static_artifacts:
        write_static_artifacts(repo_root)

    result = validate(
        mode=args.mode,
        repo_root=repo_root,
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
        fixture_path=pathlib.Path(args.fixture),
        owner_report_path=pathlib.Path(args.owner_report),
        agent_registry_path=pathlib.Path(args.agent_registry),
        algorithm_registry_path=pathlib.Path(args.algorithm_registry),
        binding_registry_path=pathlib.Path(args.binding_registry),
        consumer_registry_path=pathlib.Path(args.consumer_registry),
        agent_report_path=pathlib.Path(args.agent_report),
        algorithm_report_path=pathlib.Path(args.algorithm_report),
        binding_report_path=pathlib.Path(args.binding_report),
        consumer_report_path=pathlib.Path(args.consumer_report),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"components={report.get('component_count', 0)} "
            f"agents={report.get('agent_role_count_from_charter_registry', 0)} "
            f"families={report.get('algorithm_family_count_from_algorithm_registry', 0)} "
            f"bindings={report.get('binding_count_from_binding_registry', 0)} "
            f"allowed={report.get('consumer_allowed_attempt_count', 0)} "
            f"qtt_internal_ready={report.get('qtt_internal_agent_algorithm_ready', None)} "
            f"final_ready={report.get('final_ready', None)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
