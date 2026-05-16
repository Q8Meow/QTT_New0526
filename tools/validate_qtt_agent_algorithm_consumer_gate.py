#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_qtt_agent_algorithm_binding_registry as binding_gate  # noqa: E402
from tools.build_master_plan_section_coverage_report import RegistryParseError  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "agent_algorithm"
    / "qtt_agent_algorithm_consumer_gate.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agent_algorithm"
    / "QTTAgentAlgorithmConsumerGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "agent_algorithm"
    / "synthetic_qtt_agent_algorithm_consumer_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentAlgorithmConsumerGate.report.json"
)

AGENT_CHARTER_REGISTRY = binding_gate.AGENT_CHARTER_REGISTRY
ALGORITHM_FORMULA_FAMILY_REGISTRY = binding_gate.ALGORITHM_FORMULA_FAMILY_REGISTRY
AGENT_ALGORITHM_BINDING_REGISTRY = binding_gate.DEFAULT_REGISTRY
MASTER_PLAN = binding_gate.MASTER_PLAN
CANONICAL_BUNDLE = binding_gate.CANONICAL_BUNDLE
CANONICAL_BUNDLE_SHA = binding_gate.CANONICAL_BUNDLE_SHA

REGISTRY_TYPE = "QTT_AGENT_ALGORITHM_CONSUMER_GATE"
REGISTRY_VERSION = "v1"
REPORT_TYPE = "QTT_AGENT_ALGORITHM_CONSUMER_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = binding_gate.DETERMINISTIC_GENERATED_AT
SOURCE_OF_GATE_SUBSTANCE = MASTER_PLAN.as_posix()
GATE_GENERATION_POLICY = (
    "ONE_ALLOWED_ATTEMPT_PER_AGENT_ALGORITHM_BINDING_PLUS_STATIC_BLOCK_AND_OWNER_OVERRIDE_CASES"
)
ARCHITECTURE_EMPHASIS = (
    "INSTITUTIONAL_AGENT_ALGORITHM_CONSUMER_GATE_NOT_LOOSE_EXAMPLES"
)
OWNER_OVERRIDE_SATISFACTION_BASIS = binding_gate.OWNER_OVERRIDE_SATISFACTION_BASIS
STATIC_FORWARD_REFERENCE_ONLY = binding_gate.STATIC_FORWARD_REFERENCE_ONLY
SUCCESS_MARKER = "QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK"
FAILURE_MARKER = "QTT_AGENT_ALGORITHM_CONSUMER_GATE_FAILED"
FINAL_INCOMPLETE_MARKER = "QTT_AGENT_ALGORITHM_CONSUMER_GATE_FINAL_INCOMPLETE"

ATTEMPT_TYPE_ALLOWED = "ALLOWED_BOUND_CONSUMPTION"
GATE_DECISIONS = (
    "ALLOW",
    "BLOCK",
    "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
)
ATTEMPT_TYPES = (
    ATTEMPT_TYPE_ALLOWED,
    "BLOCKED_MISSING_BINDING",
    "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
    "BLOCKED_UNAUTHORIZED_TRADE_CONTEXT",
    "BLOCKED_DIRECT_ORDER_AUTHORITY",
    "BLOCKED_METADATA_MISMATCH",
    "OWNER_OVERRIDE_MISSING_BINDING",
    "OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS",
    "OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT",
    "OWNER_OVERRIDE_METADATA_MISMATCH",
)
OWNER_OVERRIDE_RESULTS = (
    "NOT_APPLICABLE",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_OVERRIDE_NOT_PRESENT",
)

TOP_FIELDS = (
    "registry_type",
    "registry_version",
    "deterministic_output",
    "generated_at_utc",
    "source_of_gate_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "agent_algorithm_binding_registry_dependency",
    "gate_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "algorithm_formula_family_registry_used_for_family_validation",
    "agent_algorithm_binding_registry_used_for_binding_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr67_is_scope_boundary_not_runtime_consumer_authority",
    "architecture_emphasis",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "normal_binding_required_for_consumption",
    "normal_consumer_class_required_for_consumption",
    "normal_trade_context_required_for_consumption",
    "missing_binding_owner_override_supported",
    "owner_override_satisfies_missing_binding_for_internal_workflow",
    "binding_row_fabrication_by_owner_override_allowed",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "static_agent_algorithm_consumer_gate_created",
    "agent_algorithm_cumulative_readiness_gate_created",
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
    "consumer_attempts",
)

FIXTURE_EXTRA_FIELDS = (
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "mode",
    "execution",
)

ATTEMPT_FIELDS = (
    "attempt_id",
    "attempt_type",
    "attempt_description",
    "agent_role",
    "agent_role_id",
    "algorithm_family_name",
    "algorithm_family_id",
    "binding_id",
    "requested_consumer_class",
    "requested_trade_context",
    "binding_exists",
    "agent_role_valid",
    "agent_role_id_matches",
    "algorithm_family_valid",
    "algorithm_family_id_matches",
    "agent_authorized_by_algorithm_family",
    "consumer_class_authorized_by_binding",
    "trade_context_authorized_by_binding",
    "direct_order_submission_allowed_by_binding",
    "runtime_live_order_authority_created_by_binding",
    "owner_override_present",
    "owner_override_basis",
    "owner_override_satisfaction_result",
    "binding_row_fabricated_by_owner_override",
    "gate_decision",
    "reason_codes",
    "authorized_consumer_classes_from_binding",
    "trade_context_applicability_from_binding",
    "input_parameter_families",
    "output_signal_type",
    "output_artifact_types",
    "family_category",
    "classical_or_quantum",
    "optimizer_compatibility",
    "quantum_applicability",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "deterministic_selection_role",
    "scoring_ranking_role",
    "quantum_classical_arbitration_role",
    "strongest_classical_comparator_required",
    "fallback_bundle_required",
    "replay_paper_evidence_required_before_advantage_claim",
    "live_evidence_required_before_profit_claim",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
    "external_fact_claim_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "profit_evidence_claim_created",
    "quantum_backend_artifact_created",
    "master_plan_doctrine_terms_used",
    "consumer_gate_derivation_summary",
    "final_qtt_internal_status",
)

ARRAY_ATTEMPT_FIELDS = {
    "reason_codes",
    "authorized_consumer_classes_from_binding",
    "trade_context_applicability_from_binding",
    "input_parameter_families",
    "output_artifact_types",
    "optimizer_compatibility",
    "quantum_applicability",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "master_plan_doctrine_terms_used",
}

ATTEMPT_FALSE_ARTIFACT_FIELDS = (
    "external_fact_claim_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "profit_evidence_claim_created",
    "quantum_backend_artifact_created",
)

TOP_FALSE_AUTHORITY_FIELDS = (
    "binding_row_fabrication_by_owner_override_allowed",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "agent_algorithm_cumulative_readiness_gate_created",
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

TOP_TRUE_AUTHORITY_FIELDS = (
    "deterministic_output",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "algorithm_formula_family_registry_used_for_family_validation",
    "agent_algorithm_binding_registry_used_for_binding_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr67_is_scope_boundary_not_runtime_consumer_authority",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "normal_binding_required_for_consumption",
    "normal_consumer_class_required_for_consumption",
    "normal_trade_context_required_for_consumption",
    "missing_binding_owner_override_supported",
    "owner_override_satisfies_missing_binding_for_internal_workflow",
    "quantum_forward_design_supported",
    "static_agent_algorithm_consumer_gate_created",
)

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_gate_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "agent_algorithm_binding_registry_dependency",
    "gate_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "algorithm_formula_family_registry_used_for_family_validation",
    "agent_algorithm_binding_registry_used_for_binding_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr67_is_scope_boundary_not_runtime_consumer_authority",
    "architecture_emphasis",
    "agent_role_count_from_charter_registry",
    "algorithm_family_count_from_algorithm_registry",
    "binding_count_from_binding_registry",
    "expected_allowed_attempt_count_from_binding_registry",
    "actual_allowed_attempt_count",
    "missing_allowed_attempt_count",
    "unexpected_allowed_attempt_count",
    "blocked_attempt_count",
    "owner_override_attempt_count",
    "invalid_agent_role_attempt_count",
    "invalid_algorithm_family_attempt_count",
    "invalid_binding_attempt_count",
    "invalid_consumer_class_authorization_count",
    "invalid_trade_context_authorization_count",
    "attempts_with_duplicate_id_count",
    "allowed_attempts_with_owner_override_count",
    "blocked_attempts_with_owner_override_count",
    "owner_override_attempts_without_satisfaction_count",
    "owner_override_attempts_fabricating_binding_rows_count",
    "missing_binding_block_covered",
    "unauthorized_consumer_class_block_covered",
    "unauthorized_trade_context_block_covered",
    "owner_override_missing_binding_covered",
    "owner_override_unauthorized_consumer_class_covered",
    "owner_override_unauthorized_trade_context_covered",
    "quantum_forward_design_supported",
    "quantum_or_quantum_compatible_allowed_attempt_count",
    "quantum_allowed_attempts_with_owner_quantum_priority_supported_count",
    "quantum_allowed_attempts_with_owner_can_force_quantum_priority_count",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_evidence_claim_created",
    "static_agent_algorithm_consumer_gate_created",
    "agent_algorithm_cumulative_readiness_gate_created",
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
    "authority_boundary_all_false",
)

REPORT_INTEGER_FIELDS = {
    field for field in REPORT_FIELDS if field.endswith("_count") or "_count_" in field
}

QUANTUM_CLASS_VALUES = {
    "TRUE_QUANTUM",
    "QUANTUM_INSPIRED",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUANTUM_COMPATIBLE",
    "TRUE_QUANTUM_COMPATIBLE",
    "TRUE_QUANTUM_OR_QUANTUM_INSPIRED_COMPATIBLE",
}
QUANTUM_COMPATIBILITY_TOKENS = {
    "TRUE_QUANTUM",
    "QUANTUM_INSPIRED",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUBO_COMPATIBLE",
    "ISING_COMPATIBLE",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
}

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
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
    if not path.exists():
        return None, [f"registry file is missing: {path}"]
    try:
        return load_registry(path), []
    except (json.JSONDecodeError, RegistryParseError, ValueError) as exc:
        return None, [f"registry file is invalid: {path}: {exc}"]


def _registry_items(
    registry: dict[str, Any] | None,
    field: str,
    label: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    if registry is None:
        return [], []
    items = registry.get(field)
    if not isinstance(items, list):
        return [], [f"{label}.{field} must be a list"]
    failures: list[str] = []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(f"{label}.{field}[{index}] must be an object")
            continue
        rows.append(item)
    return rows, failures


def _agent_charters_by_role(
    registry: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    return binding_gate._agent_charters_by_role(registry)


def _algorithm_families_by_name(
    registry: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[str]]:
    return binding_gate._algorithm_families_by_name(registry)


def _bindings_by_id(
    registry: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[str]]:
    bindings, failures = _registry_items(
        registry,
        "agent_algorithm_bindings",
        "binding registry",
    )
    by_id: dict[str, dict[str, Any]] = {}
    for index, binding in enumerate(bindings):
        binding_id = binding.get("binding_id")
        if not isinstance(binding_id, str) or not binding_id:
            failures.append(
                f"binding registry.agent_algorithm_bindings[{index}].binding_id is invalid"
            )
            continue
        if binding_id in by_id:
            failures.append(f"binding registry duplicate binding_id {binding_id}")
        by_id[binding_id] = binding
    return by_id, bindings, failures


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _required_string(value: Any, default: str = STATIC_FORWARD_REFERENCE_ONLY) -> str:
    return value if isinstance(value, str) and value else default


def _first_string(value: Any) -> str:
    values = _string_list(value)
    return values[0] if values else STATIC_FORWARD_REFERENCE_ONLY


def _is_quantum_or_quantum_compatible(attempt: dict[str, Any]) -> bool:
    classical_or_quantum = str(attempt.get("classical_or_quantum") or "")
    if classical_or_quantum in QUANTUM_CLASS_VALUES:
        return True
    for field in (
        "optimizer_compatibility",
        "quantum_applicability",
        "quantum_algorithm_family_access",
        "quantum_parameter_family_access",
    ):
        if QUANTUM_COMPATIBILITY_TOKENS & set(_string_list(attempt.get(field))):
            return True
    return False


def attempt_id_for_allowed(
    index: int,
    *,
    agent_role: str,
    algorithm_family_name: str,
) -> str:
    return (
        f"QTT_AGENT_ALGORITHM_CONSUMER_ATTEMPT_ALLOW_{index:03d}_"
        f"{agent_role}__{algorithm_family_name}"
    )


def attempt_id_for_blocked(index: int, reason_code: str) -> str:
    return f"QTT_AGENT_ALGORITHM_CONSUMER_ATTEMPT_BLOCK_{index:03d}_{reason_code}"


def attempt_id_for_owner_override(index: int, reason_code: str) -> str:
    return (
        f"QTT_AGENT_ALGORITHM_CONSUMER_ATTEMPT_OWNER_OVERRIDE_{index:03d}_"
        f"{reason_code}"
    )


def _base_top_level(*, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "registry_type": REGISTRY_TYPE,
        "registry_version": REGISTRY_VERSION,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_gate_substance": SOURCE_OF_GATE_SUBSTANCE,
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "agent_algorithm_binding_registry_dependency": (
            AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        ),
        "gate_generation_policy": GATE_GENERATION_POLICY,
        "master_plan_followed_as_controlling_doctrine": True,
        "agent_charter_registry_used_for_role_validation": True,
        "algorithm_formula_family_registry_used_for_family_validation": True,
        "agent_algorithm_binding_registry_used_for_binding_validation": True,
        "existing_pr_patterns_used_for_style_only": True,
        "pr67_is_scope_boundary_not_runtime_consumer_authority": True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "owner_global_override_authority": True,
        "owner_override_satisfies_all_qtt_internal_requirements": True,
        "normal_binding_required_for_consumption": True,
        "normal_consumer_class_required_for_consumption": True,
        "normal_trade_context_required_for_consumption": True,
        "missing_binding_owner_override_supported": True,
        "owner_override_satisfies_missing_binding_for_internal_workflow": True,
        "binding_row_fabrication_by_owner_override_allowed": False,
        "chatgpt_authority_over_owner": False,
        "codex_authority_over_owner": False,
        "qtt_agent_authority_over_owner": False,
        "quantum_forward_design_supported": True,
        "quantum_evidence_claim_created": False,
        "alpha_evidence_claim_created": False,
        "profit_evidence_claim_created": False,
        "latency_superiority_evidence_claim_created": False,
        "execution_superiority_evidence_claim_created": False,
        "static_agent_algorithm_consumer_gate_created": True,
        "agent_algorithm_cumulative_readiness_gate_created": False,
        "agent_algorithm_command_matrix_created": False,
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
        "consumer_attempts": attempts,
    }


def _attempt_from_binding(
    *,
    attempt_id: str,
    attempt_type: str,
    attempt_description: str,
    binding: dict[str, Any],
    agent_charter: dict[str, Any] | None,
    family: dict[str, Any] | None,
    binding_exists: bool,
    requested_consumer_class: str,
    requested_trade_context: str,
    gate_decision: str,
    owner_override_present: bool,
    reason_codes: list[str],
    agent_role: str | None = None,
    agent_role_id: str | None = None,
    algorithm_family_name: str | None = None,
    algorithm_family_id: str | None = None,
) -> dict[str, Any]:
    role = _required_string(agent_role or binding.get("agent_role"))
    role_id = _required_string(agent_role_id or binding.get("agent_role_id"))
    family_name = _required_string(
        algorithm_family_name or binding.get("algorithm_family_name")
    )
    family_id = _required_string(algorithm_family_id or binding.get("algorithm_family_id"))
    source = binding if binding_exists else (family or {})
    authorized_classes = (
        _string_list(binding.get("authorized_consumer_classes"))
        if binding_exists
        else [STATIC_FORWARD_REFERENCE_ONLY]
    )
    trade_contexts = (
        _string_list(binding.get("trade_context_applicability"))
        if binding_exists
        else [STATIC_FORWARD_REFERENCE_ONLY]
    )
    role_valid = agent_charter is not None
    family_valid = family is not None
    agent_authorized = (
        role in _string_list(family.get("authorized_agent_roles"))
        if isinstance(family, dict)
        else False
    )
    owner_override_result = (
        "OWNER_OVERRIDE_SATISFIED"
        if owner_override_present
        else ("NOT_APPLICABLE" if gate_decision == "ALLOW" else "OWNER_OVERRIDE_NOT_PRESENT")
    )
    owner_override_basis = (
        "OWNER_GLOBAL_OVERRIDE"
        if owner_override_present
        else "NOT_APPLICABLE"
    )
    final_status = {
        "ALLOW": "STATIC_BOUND_CONSUMPTION_ALLOWED_NOT_FINAL_READY",
        "BLOCK": "STATIC_CONSUMPTION_BLOCKED_FAIL_CLOSED",
        "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW": (
            "OWNER_OVERRIDE_SATISFIED_INTERNAL_WORKFLOW_NOT_RUNTIME_AUTHORITY"
        ),
    }[gate_decision]

    return {
        "attempt_id": attempt_id,
        "attempt_type": attempt_type,
        "attempt_description": attempt_description,
        "agent_role": role,
        "agent_role_id": role_id,
        "algorithm_family_name": family_name,
        "algorithm_family_id": family_id,
        "binding_id": _required_string(binding.get("binding_id")),
        "requested_consumer_class": requested_consumer_class,
        "requested_trade_context": requested_trade_context,
        "binding_exists": binding_exists,
        "agent_role_valid": role_valid,
        "agent_role_id_matches": (
            role_valid and role_id == agent_charter.get("agent_role_id")
        ),
        "algorithm_family_valid": family_valid,
        "algorithm_family_id_matches": (
            family_valid and family_id == family.get("algorithm_family_id")
        ),
        "agent_authorized_by_algorithm_family": agent_authorized,
        "consumer_class_authorized_by_binding": (
            binding_exists and requested_consumer_class in authorized_classes
        ),
        "trade_context_authorized_by_binding": (
            binding_exists and requested_trade_context in trade_contexts
        ),
        "direct_order_submission_allowed_by_binding": (
            binding_exists and binding.get("direct_order_submission_allowed") is True
        ),
        "runtime_live_order_authority_created_by_binding": (
            binding_exists
            and binding.get("runtime_live_order_authority_created") is True
        ),
        "owner_override_present": owner_override_present,
        "owner_override_basis": owner_override_basis,
        "owner_override_satisfaction_result": owner_override_result,
        "binding_row_fabricated_by_owner_override": False,
        "gate_decision": gate_decision,
        "reason_codes": reason_codes,
        "authorized_consumer_classes_from_binding": authorized_classes,
        "trade_context_applicability_from_binding": trade_contexts,
        "input_parameter_families": _string_list(source.get("input_parameter_families"))
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "output_signal_type": _required_string(source.get("output_signal_type")),
        "output_artifact_types": _string_list(source.get("output_artifact_types"))
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "family_category": _required_string(source.get("family_category")),
        "classical_or_quantum": _required_string(source.get("classical_or_quantum")),
        "optimizer_compatibility": _string_list(source.get("optimizer_compatibility"))
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "quantum_applicability": _string_list(source.get("quantum_applicability"))
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "quantum_algorithm_family_access": _string_list(
            source.get("quantum_algorithm_family_access")
        )
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "quantum_parameter_family_access": _string_list(
            source.get("quantum_parameter_family_access")
        )
        or [STATIC_FORWARD_REFERENCE_ONLY],
        "deterministic_selection_role": _required_string(
            source.get("deterministic_selection_role")
        ),
        "scoring_ranking_role": _required_string(source.get("scoring_ranking_role")),
        "quantum_classical_arbitration_role": _required_string(
            source.get("quantum_classical_arbitration_role")
        ),
        "strongest_classical_comparator_required": (
            source.get("strongest_classical_comparator_required") is True
        ),
        "fallback_bundle_required": source.get("fallback_bundle_required") is True,
        "replay_paper_evidence_required_before_advantage_claim": (
            source.get("replay_paper_evidence_required_before_advantage_claim") is True
        ),
        "live_evidence_required_before_profit_claim": (
            source.get("live_evidence_required_before_profit_claim") is True
        ),
        "owner_quantum_priority_supported": (
            source.get("owner_quantum_priority_supported") is True
        ),
        "owner_can_force_quantum_priority": (
            source.get("owner_can_force_quantum_priority") is True
        ),
        "external_fact_claim_created": False,
        "source_acceptance_artifact_created": False,
        "connector_binding_artifact_created": False,
        "runtime_resolver_snapshot_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "runtime_artifact_created": False,
        "live_artifact_created": False,
        "order_artifact_created": False,
        "profit_evidence_claim_created": False,
        "quantum_backend_artifact_created": False,
        "master_plan_doctrine_terms_used": _string_list(
            binding.get("master_plan_doctrine_terms_used")
        )
        or _string_list(source.get("master_plan_doctrine_terms_used"))
        or [
            "agent",
            "algorithm",
            "binding",
            "consumer boundary",
            "owner override",
            "execution router final order authority",
        ],
        "consumer_gate_derivation_summary": (
            "Static consumer gate evaluation derived from canonical agent role, "
            "algorithm family, and agent-algorithm binding registries; no runtime, "
            "live, order, source-acceptance, profit, or quantum-backend authority is created."
        ),
        "final_qtt_internal_status": final_status,
    }


def _missing_binding_attempt(
    *,
    attempt_id: str,
    attempt_type: str,
    gate_decision: str,
    owner_override_present: bool,
    role: str,
    family_name: str,
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
    requested_consumer_class: str,
    requested_trade_context: str,
    reason_codes: list[str],
) -> dict[str, Any]:
    family = families_by_name[family_name]
    missing_binding = {
        "binding_id": f"NO_CANONICAL_BINDING_ROW_{role}__{family_name}",
        "agent_role": role,
        "agent_role_id": _required_string(
            charters_by_role.get(role, {}).get("agent_role_id")
        ),
        "algorithm_family_name": family_name,
        "algorithm_family_id": _required_string(family.get("algorithm_family_id")),
    }
    return _attempt_from_binding(
        attempt_id=attempt_id,
        attempt_type=attempt_type,
        attempt_description=(
            "No canonical static binding exists for the requested agent-role and "
            "algorithm-family pair."
        ),
        binding=missing_binding,
        agent_charter=charters_by_role.get(role),
        family=family,
        binding_exists=False,
        requested_consumer_class=requested_consumer_class,
        requested_trade_context=requested_trade_context,
        gate_decision=gate_decision,
        owner_override_present=owner_override_present,
        reason_codes=reason_codes,
    )


def _build_allowed_attempt(
    *,
    index: int,
    binding: dict[str, Any],
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    role = _required_string(binding.get("agent_role"))
    family_name = _required_string(binding.get("algorithm_family_name"))
    return _attempt_from_binding(
        attempt_id=attempt_id_for_allowed(
            index,
            agent_role=role,
            algorithm_family_name=family_name,
        ),
        attempt_type=ATTEMPT_TYPE_ALLOWED,
        attempt_description=(
            "Canonical binding-backed static consumption attempt using the first "
            "deterministic consumer class and trade context authorized by the binding."
        ),
        binding=binding,
        agent_charter=charters_by_role.get(role),
        family=families_by_name.get(family_name),
        binding_exists=True,
        requested_consumer_class=_first_string(binding.get("authorized_consumer_classes")),
        requested_trade_context=_first_string(binding.get("trade_context_applicability")),
        gate_decision="ALLOW",
        owner_override_present=False,
        reason_codes=["CANONICAL_BINDING_CONSUMPTION_ALLOWED"],
    )


def _find_binding(
    bindings: Sequence[dict[str, Any]],
    *,
    family_name: str | None = None,
    consumer_class: str | None = None,
) -> dict[str, Any]:
    for binding in bindings:
        if family_name is not None and binding.get("algorithm_family_name") != family_name:
            continue
        if consumer_class is not None and consumer_class not in _string_list(
            binding.get("authorized_consumer_classes")
        ):
            continue
        return binding
    raise ValueError("required synthetic gate binding seed was not found")


def _build_blocked_attempts(
    *,
    bindings: Sequence[dict[str, Any]],
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    first = bindings[0]
    execution_binding = _find_binding(bindings, consumer_class="ORDER_ROUTER")
    metadata_binding = bindings[1]
    owner_role = "OWNER"
    signal_family = "CLASSICAL_SIGNAL_ALGORITHM"
    wrong_role_id = _required_string(charters_by_role[owner_role].get("agent_role_id"))
    wrong_family_id = _required_string(
        families_by_name["CLASSICAL_SCORING_ALGORITHM"].get("algorithm_family_id")
    )

    return [
        _missing_binding_attempt(
            attempt_id=attempt_id_for_blocked(1, "MISSING_BINDING"),
            attempt_type="BLOCKED_MISSING_BINDING",
            gate_decision="BLOCK",
            owner_override_present=False,
            role=owner_role,
            family_name=signal_family,
            charters_by_role=charters_by_role,
            families_by_name=families_by_name,
            requested_consumer_class=_first_string(first.get("authorized_consumer_classes")),
            requested_trade_context=_first_string(first.get("trade_context_applicability")),
            reason_codes=["MISSING_CANONICAL_AGENT_ALGORITHM_BINDING"],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_blocked(2, "UNAUTHORIZED_CONSUMER_CLASS"),
            attempt_type="BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            attempt_description=(
                "Binding exists, but the requested consumer class is not declared "
                "by the canonical binding."
            ),
            binding=first,
            agent_charter=charters_by_role.get(str(first.get("agent_role"))),
            family=families_by_name.get(str(first.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class="UNAUTHORIZED_CONSUMER_CLASS_FOR_GATE",
            requested_trade_context=_first_string(first.get("trade_context_applicability")),
            gate_decision="BLOCK",
            owner_override_present=False,
            reason_codes=["REQUESTED_CONSUMER_CLASS_NOT_AUTHORIZED_BY_BINDING"],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_blocked(3, "UNAUTHORIZED_TRADE_CONTEXT"),
            attempt_type="BLOCKED_UNAUTHORIZED_TRADE_CONTEXT",
            attempt_description=(
                "Binding exists, but the requested trade context is not declared "
                "by the canonical binding."
            ),
            binding=first,
            agent_charter=charters_by_role.get(str(first.get("agent_role"))),
            family=families_by_name.get(str(first.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class=_first_string(first.get("authorized_consumer_classes")),
            requested_trade_context="UNAUTHORIZED_TRADE_CONTEXT_FOR_GATE",
            gate_decision="BLOCK",
            owner_override_present=False,
            reason_codes=["REQUESTED_TRADE_CONTEXT_NOT_AUTHORIZED_BY_BINDING"],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_blocked(4, "DIRECT_ORDER_AUTHORITY"),
            attempt_type="BLOCKED_DIRECT_ORDER_AUTHORITY",
            attempt_description=(
                "Static consumption may inspect an order-router class binding, but "
                "the consumer gate blocks any implication of direct order submission "
                "or runtime live authority."
            ),
            binding=execution_binding,
            agent_charter=charters_by_role.get(str(execution_binding.get("agent_role"))),
            family=families_by_name.get(
                str(execution_binding.get("algorithm_family_name"))
            ),
            binding_exists=True,
            requested_consumer_class=_first_string(
                execution_binding.get("authorized_consumer_classes")
            ),
            requested_trade_context=_first_string(
                execution_binding.get("trade_context_applicability")
            ),
            gate_decision="BLOCK",
            owner_override_present=False,
            reason_codes=[
                "DIRECT_ORDER_SUBMISSION_AUTHORITY_NOT_CREATED_BY_STATIC_CONSUMER_GATE",
                "EXECUTION_ROUTER_REMAINS_FINAL_ORDER_SUBMISSION_AUTHORITY",
            ],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_blocked(5, "METADATA_MISMATCH"),
            attempt_type="BLOCKED_METADATA_MISMATCH",
            attempt_description=(
                "Binding row exists, but the requested metadata conflicts with "
                "dependency registry identifiers."
            ),
            binding=metadata_binding,
            agent_charter=charters_by_role.get(str(metadata_binding.get("agent_role"))),
            family=families_by_name.get(str(metadata_binding.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class=_first_string(
                metadata_binding.get("authorized_consumer_classes")
            ),
            requested_trade_context=_first_string(
                metadata_binding.get("trade_context_applicability")
            ),
            gate_decision="BLOCK",
            owner_override_present=False,
            reason_codes=["BINDING_METADATA_CONFLICTS_WITH_DEPENDENCY_REGISTRIES"],
            agent_role_id=wrong_role_id,
            algorithm_family_id=wrong_family_id,
        ),
    ]


def _build_owner_override_attempts(
    *,
    bindings: Sequence[dict[str, Any]],
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    first = bindings[0]
    metadata_binding = bindings[2]
    quantum_missing_role = "QUANTUM_BACKEND_AGENT"
    quantum_missing_family = "CLASSICAL_SIGNAL_ALGORITHM"
    wrong_role_id = _required_string(
        charters_by_role["OWNER"].get("agent_role_id")
    )
    wrong_family_id = _required_string(
        families_by_name["CLASSICAL_SCORING_ALGORITHM"].get("algorithm_family_id")
    )
    return [
        _missing_binding_attempt(
            attempt_id=attempt_id_for_owner_override(1, "MISSING_BINDING"),
            attempt_type="OWNER_OVERRIDE_MISSING_BINDING",
            gate_decision="OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
            owner_override_present=True,
            role="OWNER",
            family_name="CLASSICAL_SIGNAL_ALGORITHM",
            charters_by_role=charters_by_role,
            families_by_name=families_by_name,
            requested_consumer_class=_first_string(first.get("authorized_consumer_classes")),
            requested_trade_context=_first_string(first.get("trade_context_applicability")),
            reason_codes=[
                "OWNER_OVERRIDE_SATISFIES_MISSING_BINDING_INTERNAL_WORKFLOW_BLOCKER"
            ],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_owner_override(2, "UNAUTHORIZED_CONSUMER_CLASS"),
            attempt_type="OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS",
            attempt_description=(
                "Owner override satisfies the internal workflow blocker for an "
                "unauthorized consumer-class request without changing the binding."
            ),
            binding=first,
            agent_charter=charters_by_role.get(str(first.get("agent_role"))),
            family=families_by_name.get(str(first.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class="UNAUTHORIZED_CONSUMER_CLASS_FOR_GATE",
            requested_trade_context=_first_string(first.get("trade_context_applicability")),
            gate_decision="OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
            owner_override_present=True,
            reason_codes=[
                "OWNER_OVERRIDE_SATISFIES_CONSUMER_CLASS_INTERNAL_WORKFLOW_BLOCKER"
            ],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_owner_override(3, "UNAUTHORIZED_TRADE_CONTEXT"),
            attempt_type="OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT",
            attempt_description=(
                "Owner override satisfies the internal workflow blocker for an "
                "unauthorized trade-context request without changing the binding."
            ),
            binding=first,
            agent_charter=charters_by_role.get(str(first.get("agent_role"))),
            family=families_by_name.get(str(first.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class=_first_string(first.get("authorized_consumer_classes")),
            requested_trade_context="UNAUTHORIZED_TRADE_CONTEXT_FOR_GATE",
            gate_decision="OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
            owner_override_present=True,
            reason_codes=[
                "OWNER_OVERRIDE_SATISFIES_TRADE_CONTEXT_INTERNAL_WORKFLOW_BLOCKER"
            ],
        ),
        _attempt_from_binding(
            attempt_id=attempt_id_for_owner_override(4, "METADATA_MISMATCH"),
            attempt_type="OWNER_OVERRIDE_METADATA_MISMATCH",
            attempt_description=(
                "Owner override satisfies the internal workflow blocker for "
                "metadata mismatch without fabricating corrected registry metadata."
            ),
            binding=metadata_binding,
            agent_charter=charters_by_role.get(str(metadata_binding.get("agent_role"))),
            family=families_by_name.get(str(metadata_binding.get("algorithm_family_name"))),
            binding_exists=True,
            requested_consumer_class=_first_string(
                metadata_binding.get("authorized_consumer_classes")
            ),
            requested_trade_context=_first_string(
                metadata_binding.get("trade_context_applicability")
            ),
            gate_decision="OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
            owner_override_present=True,
            reason_codes=[
                "OWNER_OVERRIDE_SATISFIES_METADATA_MISMATCH_INTERNAL_WORKFLOW_BLOCKER"
            ],
            agent_role_id=wrong_role_id,
            algorithm_family_id=wrong_family_id,
        ),
        _missing_binding_attempt(
            attempt_id=attempt_id_for_owner_override(5, "MISSING_BINDING_QUANTUM_SCOPE"),
            attempt_type="OWNER_OVERRIDE_MISSING_BINDING",
            gate_decision="OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW",
            owner_override_present=True,
            role=quantum_missing_role,
            family_name=quantum_missing_family,
            charters_by_role=charters_by_role,
            families_by_name=families_by_name,
            requested_consumer_class=_first_string(first.get("authorized_consumer_classes")),
            requested_trade_context=_first_string(first.get("trade_context_applicability")),
            reason_codes=[
                "OWNER_OVERRIDE_SATISFIES_MISSING_BINDING_INTERNAL_WORKFLOW_BLOCKER",
                "OWNER_OVERRIDE_DOES_NOT_CREATE_QUANTUM_BACKEND_ARTIFACT",
            ],
        ),
    ]


def build_registry_from_dependencies(
    *,
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    binding_registry: dict[str, Any],
    synthetic: bool,
) -> dict[str, Any]:
    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    families_by_name, _, family_failures = _algorithm_families_by_name(
        algorithm_registry
    )
    _, bindings, binding_failures = _bindings_by_id(binding_registry)
    failures = [*charter_failures, *family_failures, *binding_failures]
    if failures:
        raise ValueError("; ".join(failures))

    allowed = [
        _build_allowed_attempt(
            index=index,
            binding=binding,
            charters_by_role=charters_by_role,
            families_by_name=families_by_name,
        )
        for index, binding in enumerate(bindings, start=1)
    ]
    blocked = _build_blocked_attempts(
        bindings=bindings,
        charters_by_role=charters_by_role,
        families_by_name=families_by_name,
    )
    owner_override = _build_owner_override_attempts(
        bindings=bindings,
        charters_by_role=charters_by_role,
        families_by_name=families_by_name,
    )
    attempts = (
        [
            allowed[0],
            blocked[0],
            blocked[1],
            blocked[2],
            owner_override[0],
            owner_override[1],
            owner_override[2],
        ]
        if synthetic
        else [*allowed, *blocked, *owner_override]
    )
    registry = _base_top_level(attempts=attempts)
    if synthetic:
        registry.update(
            {
                "fixture_id": "synthetic_qtt_agent_algorithm_consumer_gate_v1",
                "fixture_version": "v1",
                "fixture_authority_class": (
                    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_AGENT_ALGORITHM_CONSUMER_AUTHORITY"
                ),
                "mode": "SOURCE_REQUIRED",
                "execution": "DISABLED",
            }
        )
    return registry


def _schema_nonempty_string() -> dict[str, Any]:
    return {"type": "string", "minLength": 1}


def _schema_string_array() -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": 1,
        "items": _schema_nonempty_string(),
    }


def build_schema(
    *,
    agent_roles: Sequence[str],
    agent_role_ids: Sequence[str],
    algorithm_family_names: Sequence[str],
    algorithm_family_ids: Sequence[str],
) -> dict[str, Any]:
    attempt_properties: dict[str, Any] = {
        "attempt_id": _schema_nonempty_string(),
        "attempt_type": {"enum": list(ATTEMPT_TYPES)},
        "attempt_description": _schema_nonempty_string(),
        "agent_role": {"enum": list(agent_roles)},
        "agent_role_id": {"enum": list(agent_role_ids)},
        "algorithm_family_name": {"enum": list(algorithm_family_names)},
        "algorithm_family_id": {"enum": list(algorithm_family_ids)},
        "binding_id": _schema_nonempty_string(),
        "requested_consumer_class": _schema_nonempty_string(),
        "requested_trade_context": _schema_nonempty_string(),
        "binding_exists": {"type": "boolean"},
        "agent_role_valid": {"type": "boolean"},
        "agent_role_id_matches": {"type": "boolean"},
        "algorithm_family_valid": {"type": "boolean"},
        "algorithm_family_id_matches": {"type": "boolean"},
        "agent_authorized_by_algorithm_family": {"type": "boolean"},
        "consumer_class_authorized_by_binding": {"type": "boolean"},
        "trade_context_authorized_by_binding": {"type": "boolean"},
        "direct_order_submission_allowed_by_binding": {"type": "boolean"},
        "runtime_live_order_authority_created_by_binding": {"type": "boolean"},
        "owner_override_present": {"type": "boolean"},
        "owner_override_basis": _schema_nonempty_string(),
        "owner_override_satisfaction_result": {"enum": list(OWNER_OVERRIDE_RESULTS)},
        "binding_row_fabricated_by_owner_override": {"const": False},
        "gate_decision": {"enum": list(GATE_DECISIONS)},
        "reason_codes": _schema_string_array(),
        "authorized_consumer_classes_from_binding": _schema_string_array(),
        "trade_context_applicability_from_binding": _schema_string_array(),
        "input_parameter_families": _schema_string_array(),
        "output_signal_type": _schema_nonempty_string(),
        "output_artifact_types": _schema_string_array(),
        "family_category": _schema_nonempty_string(),
        "classical_or_quantum": _schema_nonempty_string(),
        "optimizer_compatibility": _schema_string_array(),
        "quantum_applicability": _schema_string_array(),
        "quantum_algorithm_family_access": _schema_string_array(),
        "quantum_parameter_family_access": _schema_string_array(),
        "deterministic_selection_role": _schema_nonempty_string(),
        "scoring_ranking_role": _schema_nonempty_string(),
        "quantum_classical_arbitration_role": _schema_nonempty_string(),
        "strongest_classical_comparator_required": {"type": "boolean"},
        "fallback_bundle_required": {"type": "boolean"},
        "replay_paper_evidence_required_before_advantage_claim": {
            "type": "boolean"
        },
        "live_evidence_required_before_profit_claim": {"type": "boolean"},
        "owner_quantum_priority_supported": {"type": "boolean"},
        "owner_can_force_quantum_priority": {"type": "boolean"},
        "external_fact_claim_created": {"const": False},
        "source_acceptance_artifact_created": {"const": False},
        "connector_binding_artifact_created": {"const": False},
        "runtime_resolver_snapshot_created": {"const": False},
        "replay_execution_created": {"const": False},
        "paper_execution_created": {"const": False},
        "runtime_artifact_created": {"const": False},
        "live_artifact_created": {"const": False},
        "order_artifact_created": {"const": False},
        "profit_evidence_claim_created": {"const": False},
        "quantum_backend_artifact_created": {"const": False},
        "master_plan_doctrine_terms_used": _schema_string_array(),
        "consumer_gate_derivation_summary": _schema_nonempty_string(),
        "final_qtt_internal_status": _schema_nonempty_string(),
    }

    top_properties: dict[str, Any] = {
        "registry_type": {"const": REGISTRY_TYPE},
        "registry_version": {"const": REGISTRY_VERSION},
        "deterministic_output": {"const": True},
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "source_of_gate_substance": {"const": SOURCE_OF_GATE_SUBSTANCE},
        "agent_charter_registry_dependency": {
            "const": AGENT_CHARTER_REGISTRY.as_posix()
        },
        "algorithm_formula_family_registry_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        },
        "agent_algorithm_binding_registry_dependency": {
            "const": AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        },
        "gate_generation_policy": {"const": GATE_GENERATION_POLICY},
        "master_plan_followed_as_controlling_doctrine": {"const": True},
        "agent_charter_registry_used_for_role_validation": {"const": True},
        "algorithm_formula_family_registry_used_for_family_validation": {
            "const": True
        },
        "agent_algorithm_binding_registry_used_for_binding_validation": {
            "const": True
        },
        "existing_pr_patterns_used_for_style_only": {"const": True},
        "pr67_is_scope_boundary_not_runtime_consumer_authority": {"const": True},
        "architecture_emphasis": {"const": ARCHITECTURE_EMPHASIS},
        "owner_global_override_authority": {"const": True},
        "owner_override_satisfies_all_qtt_internal_requirements": {"const": True},
        "normal_binding_required_for_consumption": {"const": True},
        "normal_consumer_class_required_for_consumption": {"const": True},
        "normal_trade_context_required_for_consumption": {"const": True},
        "missing_binding_owner_override_supported": {"const": True},
        "owner_override_satisfies_missing_binding_for_internal_workflow": {
            "const": True
        },
        "binding_row_fabrication_by_owner_override_allowed": {"const": False},
        "chatgpt_authority_over_owner": {"const": False},
        "codex_authority_over_owner": {"const": False},
        "qtt_agent_authority_over_owner": {"const": False},
        "quantum_forward_design_supported": {"const": True},
        "quantum_evidence_claim_created": {"const": False},
        "alpha_evidence_claim_created": {"const": False},
        "profit_evidence_claim_created": {"const": False},
        "latency_superiority_evidence_claim_created": {"const": False},
        "execution_superiority_evidence_claim_created": {"const": False},
        "static_agent_algorithm_consumer_gate_created": {"const": True},
        "agent_algorithm_cumulative_readiness_gate_created": {"const": False},
        "agent_algorithm_command_matrix_created": {"const": False},
        "runtime_artifact_created": {"const": False},
        "live_artifact_created": {"const": False},
        "order_artifact_created": {"const": False},
        "source_acceptance_artifact_created": {"const": False},
        "connector_binding_artifact_created": {"const": False},
        "runtime_resolver_snapshot_created": {"const": False},
        "replay_execution_created": {"const": False},
        "paper_execution_created": {"const": False},
        "quantum_backend_artifact_created": {"const": False},
        "bundle_file_present": {"const": False},
        "bundle_sha_present": {"const": False},
        "uses_pr_number_as_authority": {"const": False},
        "final_ready": {"const": False},
        "consumer_attempts": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"$ref": "#/$defs/consumer_attempt"},
        },
        "fixture_id": _schema_nonempty_string(),
        "fixture_version": {"const": "v1"},
        "fixture_authority_class": _schema_nonempty_string(),
        "mode": {"const": "SOURCE_REQUIRED"},
        "execution": {"const": "DISABLED"},
    }
    report_properties: dict[str, Any] = {}
    for field in REPORT_FIELDS:
        if field == "report_type":
            report_properties[field] = {"const": REPORT_TYPE}
        elif field == "generated_at_utc":
            report_properties[field] = {"const": DETERMINISTIC_GENERATED_AT}
        elif field == "source_of_gate_substance":
            report_properties[field] = {"const": SOURCE_OF_GATE_SUBSTANCE}
        elif field == "agent_charter_registry_dependency":
            report_properties[field] = {"const": AGENT_CHARTER_REGISTRY.as_posix()}
        elif field == "algorithm_formula_family_registry_dependency":
            report_properties[field] = {
                "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
            }
        elif field == "agent_algorithm_binding_registry_dependency":
            report_properties[field] = {
                "const": AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
            }
        elif field == "gate_generation_policy":
            report_properties[field] = {"const": GATE_GENERATION_POLICY}
        elif field == "architecture_emphasis":
            report_properties[field] = {"const": ARCHITECTURE_EMPHASIS}
        elif field in REPORT_INTEGER_FIELDS:
            report_properties[field] = {"type": "integer"}
        else:
            report_properties[field] = {"type": "boolean"}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://qtt.local/schemas/agent_algorithm/"
            "qtt_agent_algorithm_consumer_gate.schema.json"
        ),
        "title": "QTT Agent Algorithm Consumer Gate",
        "description": (
            "Static deterministic QTT agent-algorithm consumer gate schema. "
            "It authorizes agent consumption of algorithm/formula families only "
            "through canonical bindings, authorized consumer classes, authorized "
            "trade contexts, or owner override for internal workflow satisfaction."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": top_properties,
        "required": list(TOP_FIELDS),
        "$defs": {
            "consumer_attempt": {
                "type": "object",
                "additionalProperties": False,
                "properties": attempt_properties,
                "required": list(ATTEMPT_FIELDS),
            },
            "agent_algorithm_consumer_gate_report": {
                "type": "object",
                "additionalProperties": False,
                "properties": report_properties,
                "required": list(REPORT_FIELDS),
            },
            "agent_role": {"enum": list(agent_roles)},
            "agent_role_id": {"enum": list(agent_role_ids)},
            "algorithm_family_name": {"enum": list(algorithm_family_names)},
            "algorithm_family_id": {"enum": list(algorithm_family_ids)},
        },
    }


def _uses_pr_number_as_authority(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number_as_authority(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number_as_authority(item) for item in value)
    return False


def _validate_schema_surface(
    schema: dict[str, Any],
    *,
    agent_roles: Sequence[str],
    agent_role_ids: Sequence[str],
    algorithm_family_names: Sequence[str],
    algorithm_family_ids: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    if schema.get("required") != list(TOP_FIELDS):
        failures.append("schema.required must match consumer gate top-level fields")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    attempt_def = defs.get("consumer_attempt")
    if not isinstance(attempt_def, dict):
        failures.append("schema.$defs.consumer_attempt must be an object")
    elif attempt_def.get("required") != list(ATTEMPT_FIELDS):
        failures.append("schema consumer_attempt.required must match attempt fields")
    report_def = defs.get("agent_algorithm_consumer_gate_report")
    if not isinstance(report_def, dict):
        failures.append(
            "schema.$defs.agent_algorithm_consumer_gate_report must be an object"
        )
    elif report_def.get("required") != list(REPORT_FIELDS):
        failures.append("schema report required fields must match report fields")
    expected_enums = {
        "agent_role": list(agent_roles),
        "agent_role_id": list(agent_role_ids),
        "algorithm_family_name": list(algorithm_family_names),
        "algorithm_family_id": list(algorithm_family_ids),
    }
    for name, expected in expected_enums.items():
        definition = defs.get(name)
        if not isinstance(definition, dict) or definition.get("enum") != expected:
            failures.append(f"schema.$defs.{name}.enum is not dependency-derived")
    return failures


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
    *,
    optional_fields: Sequence[str] = (),
) -> list[str]:
    expected = set(expected_fields) | set(optional_fields)
    failures: list[str] = []
    missing = sorted(set(expected_fields) - set(value))
    unexpected = sorted(set(value) - expected)
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
        TOP_FIELDS,
        label,
        optional_fields=FIXTURE_EXTRA_FIELDS,
    )
    expected_constants = {
        "registry_type": REGISTRY_TYPE,
        "registry_version": REGISTRY_VERSION,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_gate_substance": SOURCE_OF_GATE_SUBSTANCE,
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "agent_algorithm_binding_registry_dependency": (
            AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        ),
        "gate_generation_policy": GATE_GENERATION_POLICY,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
    }
    for field, expected in expected_constants.items():
        if value.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")
    for field in TOP_TRUE_AUTHORITY_FIELDS:
        if value.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in TOP_FALSE_AUTHORITY_FIELDS:
        if value.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if _uses_pr_number_as_authority(value):
        failures.append(f"{label} must not use a delivery label as authority")
    if schema is not None:
        failures.extend(validate_json_schema_subset(value, schema))
    return failures


def _validate_attempt_shape(attempt: dict[str, Any], *, label: str) -> list[str]:
    failures = _require_exact_fields(attempt, ATTEMPT_FIELDS, label)
    for field in ARRAY_ATTEMPT_FIELDS:
        value = attempt.get(field)
        if not isinstance(value, list) or not value:
            failures.append(f"{label}.{field} must be a non-empty array")
    for field in ATTEMPT_FALSE_ARTIFACT_FIELDS:
        if attempt.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if attempt.get("binding_row_fabricated_by_owner_override") is not False:
        failures.append(f"{label}.binding_row_fabricated_by_owner_override must be false")
    if attempt.get("direct_order_submission_allowed_by_binding") is True:
        failures.append(
            f"{label}.direct_order_submission_allowed_by_binding must remain false"
        )
    if attempt.get("runtime_live_order_authority_created_by_binding") is True:
        failures.append(
            f"{label}.runtime_live_order_authority_created_by_binding must remain false"
        )
    decision = attempt.get("gate_decision")
    owner_present = attempt.get("owner_override_present")
    if decision == "ALLOW":
        if owner_present is not False:
            failures.append(f"{label}: ALLOW must not use owner override")
        if attempt.get("binding_exists") is not True:
            failures.append(f"{label}: ALLOW requires binding_exists true")
    elif decision == "BLOCK":
        if owner_present is not False:
            failures.append(f"{label}: BLOCK must not use owner override")
    elif decision == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW":
        if owner_present is not True:
            failures.append(f"{label}: owner override decision requires owner override")
        if attempt.get("owner_override_satisfaction_result") != "OWNER_OVERRIDE_SATISFIED":
            failures.append(f"{label}: owner override decision requires satisfaction")
    else:
        failures.append(f"{label}.gate_decision is invalid")
    if owner_present is True and attempt.get(
        "owner_override_satisfaction_result"
    ) != "OWNER_OVERRIDE_SATISFIED":
        failures.append(f"{label}: owner_override_present requires satisfaction")
    return failures


def _allowed_attempt_key(attempt: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        str(attempt.get("binding_id")),
        str(attempt.get("agent_role")),
        str(attempt.get("agent_role_id")),
        str(attempt.get("algorithm_family_name")),
        str(attempt.get("algorithm_family_id")),
        str(attempt.get("requested_consumer_class")),
        str(attempt.get("requested_trade_context")),
    )


def _expected_allowed_attempt_keys(
    bindings: Sequence[dict[str, Any]],
) -> list[tuple[str, str, str, str, str, str, str]]:
    return [
        (
            _required_string(binding.get("binding_id")),
            _required_string(binding.get("agent_role")),
            _required_string(binding.get("agent_role_id")),
            _required_string(binding.get("algorithm_family_name")),
            _required_string(binding.get("algorithm_family_id")),
            _first_string(binding.get("authorized_consumer_classes")),
            _first_string(binding.get("trade_context_applicability")),
        )
        for binding in bindings
    ]


def _validate_allowed_attempt(
    *,
    attempt: dict[str, Any],
    binding: dict[str, Any],
    index: int,
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[str]:
    label = f"consumer_attempts[{index - 1}]"
    failures: list[str] = []
    expected_id = attempt_id_for_allowed(
        index,
        agent_role=str(binding.get("agent_role")),
        algorithm_family_name=str(binding.get("algorithm_family_name")),
    )
    if attempt.get("attempt_id") != expected_id:
        failures.append(f"{label}.attempt_id must be {expected_id}")
    if attempt.get("gate_decision") != "ALLOW":
        failures.append(f"{label}.gate_decision must be ALLOW")
    if attempt.get("attempt_type") != ATTEMPT_TYPE_ALLOWED:
        failures.append(f"{label}.attempt_type must be {ATTEMPT_TYPE_ALLOWED}")
    if attempt.get("owner_override_present") is not False:
        failures.append(f"{label}.owner_override_present must be false")
    if attempt.get("binding_exists") is not True:
        failures.append(f"{label}.binding_exists must be true")

    role = str(binding.get("agent_role"))
    family_name = str(binding.get("algorithm_family_name"))
    charter = charters_by_role.get(role)
    family = families_by_name.get(family_name)
    if charter is None:
        failures.append(f"{label}.agent_role does not exist in agent registry")
    elif attempt.get("agent_role_id") != charter.get("agent_role_id"):
        failures.append(f"{label}.agent_role_id does not match agent registry")
    if family is None:
        failures.append(f"{label}.algorithm_family_name does not exist")
    elif attempt.get("algorithm_family_id") != family.get("algorithm_family_id"):
        failures.append(
            f"{label}.algorithm_family_id does not match algorithm registry"
        )
    if attempt.get("requested_consumer_class") not in _string_list(
        binding.get("authorized_consumer_classes")
    ):
        failures.append(f"{label}.requested_consumer_class is not authorized")
    if attempt.get("requested_trade_context") not in _string_list(
        binding.get("trade_context_applicability")
    ):
        failures.append(f"{label}.requested_trade_context is not authorized")
    if attempt.get("agent_authorized_by_algorithm_family") is not True:
        failures.append(f"{label}.agent_authorized_by_algorithm_family must be true")
    if attempt.get("consumer_class_authorized_by_binding") is not True:
        failures.append(f"{label}.consumer_class_authorized_by_binding must be true")
    if attempt.get("trade_context_authorized_by_binding") is not True:
        failures.append(f"{label}.trade_context_authorized_by_binding must be true")
    for field in (
        "authorized_consumer_classes",
        "trade_context_applicability",
        "input_parameter_families",
        "output_signal_type",
        "output_artifact_types",
        "family_category",
        "classical_or_quantum",
        "optimizer_compatibility",
        "quantum_applicability",
        "quantum_algorithm_family_access",
        "quantum_parameter_family_access",
        "deterministic_selection_role",
        "scoring_ranking_role",
        "quantum_classical_arbitration_role",
        "strongest_classical_comparator_required",
        "fallback_bundle_required",
        "replay_paper_evidence_required_before_advantage_claim",
        "live_evidence_required_before_profit_claim",
        "owner_quantum_priority_supported",
        "owner_can_force_quantum_priority",
    ):
        attempt_field = (
            "authorized_consumer_classes_from_binding"
            if field == "authorized_consumer_classes"
            else (
                "trade_context_applicability_from_binding"
                if field == "trade_context_applicability"
                else field
            )
        )
        if attempt.get(attempt_field) != binding.get(field):
            failures.append(f"{label}.{attempt_field} must inherit binding.{field}")
    if _is_quantum_or_quantum_compatible(attempt):
        if attempt.get("owner_quantum_priority_supported") is not True:
            failures.append(
                f"{label}.owner_quantum_priority_supported must be true for quantum"
            )
        if attempt.get("owner_can_force_quantum_priority") is not True:
            failures.append(
                f"{label}.owner_can_force_quantum_priority must be true for quantum"
            )
    return failures


def _validate_attempts(
    *,
    value: dict[str, Any],
    label: str,
    strict_full_registry: bool,
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
    bindings_by_id: dict[str, dict[str, Any]],
    bindings: Sequence[dict[str, Any]],
) -> list[str]:
    attempts, failures = _registry_items(value, "consumer_attempts", label)
    seen_ids: set[str] = set()
    for index, attempt in enumerate(attempts):
        attempt_label = f"{label}.consumer_attempts[{index}]"
        failures.extend(_validate_attempt_shape(attempt, label=attempt_label))
        attempt_id = attempt.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            failures.append(f"{attempt_label}.attempt_id must be non-empty")
        elif attempt_id in seen_ids:
            failures.append(f"{attempt_label}.attempt_id is duplicated")
        seen_ids.add(str(attempt_id))

    allowed = [a for a in attempts if a.get("attempt_type") == ATTEMPT_TYPE_ALLOWED]
    blocked = [a for a in attempts if a.get("gate_decision") == "BLOCK"]
    owner_override = [
        a
        for a in attempts
        if a.get("gate_decision") == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW"
    ]

    if strict_full_registry:
        expected_keys = _expected_allowed_attempt_keys(bindings)
        actual_keys = [_allowed_attempt_key(attempt) for attempt in allowed]
        if actual_keys != expected_keys:
            failures.append(
                f"{label}.allowed attempts must exactly match binding registry order"
            )
            missing = [key for key in expected_keys if key not in actual_keys]
            unexpected = [key for key in actual_keys if key not in expected_keys]
            if missing:
                failures.append(f"{label} missing allowed attempt keys: {missing}")
            if unexpected:
                failures.append(f"{label} unexpected allowed attempt keys: {unexpected}")
        if len(allowed) != len(bindings):
            failures.append(
                f"{label}.allowed attempt count must equal binding count {len(bindings)}"
            )
        for index, (attempt, binding) in enumerate(zip(allowed, bindings), start=1):
            failures.extend(
                _validate_allowed_attempt(
                    attempt=attempt,
                    binding=binding,
                    index=index,
                    charters_by_role=charters_by_role,
                    families_by_name=families_by_name,
                )
            )
        if len(blocked) < 5:
            failures.append(f"{label} must contain at least 5 blocked attempts")
        if len(owner_override) < 5:
            failures.append(f"{label} must contain at least 5 owner override attempts")

    for index, attempt in enumerate(allowed):
        binding = bindings_by_id.get(str(attempt.get("binding_id")))
        if binding is None:
            failures.append(f"{label}.allowed[{index}] binding does not exist")
            continue
        failures.extend(
            _validate_allowed_attempt(
                attempt=attempt,
                binding=binding,
                index=index + 1,
                charters_by_role=charters_by_role,
                families_by_name=families_by_name,
            )
        )

    for index, attempt in enumerate(blocked):
        if attempt.get("gate_decision") != "BLOCK":
            failures.append(f"{label}.blocked[{index}] must be BLOCK")
        if attempt.get("owner_override_present") is not False:
            failures.append(f"{label}.blocked[{index}] must not use owner override")
        if not _string_list(attempt.get("reason_codes")):
            failures.append(f"{label}.blocked[{index}] must have reason codes")

    for index, attempt in enumerate(owner_override):
        if attempt.get("owner_override_present") is not True:
            failures.append(f"{label}.owner_override[{index}] must set owner override")
        if attempt.get("owner_override_satisfaction_result") != "OWNER_OVERRIDE_SATISFIED":
            failures.append(f"{label}.owner_override[{index}] must be satisfied")
        if attempt.get("binding_row_fabricated_by_owner_override") is not False:
            failures.append(f"{label}.owner_override[{index}] fabricated binding row")
        for field in ATTEMPT_FALSE_ARTIFACT_FIELDS:
            if attempt.get(field) is not False:
                failures.append(f"{label}.owner_override[{index}].{field} must be false")

    coverage_types = {str(attempt.get("attempt_type")) for attempt in attempts}
    required_coverages = {
        "BLOCKED_MISSING_BINDING",
        "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
        "BLOCKED_UNAUTHORIZED_TRADE_CONTEXT",
        "OWNER_OVERRIDE_MISSING_BINDING",
        "OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS",
        "OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT",
    }
    if strict_full_registry:
        required_coverages.update(
            {
                "BLOCKED_DIRECT_ORDER_AUTHORITY",
                "BLOCKED_METADATA_MISMATCH",
                "OWNER_OVERRIDE_METADATA_MISMATCH",
            }
        )
    missing_coverages = sorted(required_coverages - coverage_types)
    if missing_coverages:
        failures.append(
            f"{label} missing required attempt coverage: {', '.join(missing_coverages)}"
        )
    return failures


def build_report(
    registry: dict[str, Any],
    *,
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    binding_registry: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    charters_by_role, _ = _agent_charters_by_role(agent_registry)
    families_by_name, algorithm_families, _ = _algorithm_families_by_name(
        algorithm_registry
    )
    bindings_by_id, bindings, _ = _bindings_by_id(binding_registry)
    attempts = [
        attempt
        for attempt in registry.get("consumer_attempts", [])
        if isinstance(attempt, dict)
    ]
    allowed = [a for a in attempts if a.get("attempt_type") == ATTEMPT_TYPE_ALLOWED]
    blocked = [a for a in attempts if a.get("gate_decision") == "BLOCK"]
    owner_override = [
        a
        for a in attempts
        if a.get("gate_decision") == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW"
    ]
    expected_allowed_keys = _expected_allowed_attempt_keys(bindings)
    actual_allowed_keys = [_allowed_attempt_key(attempt) for attempt in allowed]
    duplicate_id_count = len([a.get("attempt_id") for a in attempts]) - len(
        {a.get("attempt_id") for a in attempts}
    )
    quantum_allowed = [
        attempt for attempt in allowed if _is_quantum_or_quantum_compatible(attempt)
    ]
    false_boundary_fields = (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "agent_algorithm_cumulative_readiness_gate_created",
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
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )
    authority_boundary_all_false = (
        all(registry.get(field) is False for field in false_boundary_fields)
        and all(
            attempt.get(field) is False
            for attempt in attempts
            for field in ATTEMPT_FALSE_ARTIFACT_FIELDS
        )
        and all(
            attempt.get("binding_row_fabricated_by_owner_override") is False
            for attempt in attempts
        )
    )
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_gate_substance": SOURCE_OF_GATE_SUBSTANCE,
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "agent_algorithm_binding_registry_dependency": (
            AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
        ),
        "gate_generation_policy": GATE_GENERATION_POLICY,
        "master_plan_followed_as_controlling_doctrine": registry.get(
            "master_plan_followed_as_controlling_doctrine"
        )
        is True,
        "agent_charter_registry_used_for_role_validation": registry.get(
            "agent_charter_registry_used_for_role_validation"
        )
        is True,
        "algorithm_formula_family_registry_used_for_family_validation": registry.get(
            "algorithm_formula_family_registry_used_for_family_validation"
        )
        is True,
        "agent_algorithm_binding_registry_used_for_binding_validation": registry.get(
            "agent_algorithm_binding_registry_used_for_binding_validation"
        )
        is True,
        "existing_pr_patterns_used_for_style_only": registry.get(
            "existing_pr_patterns_used_for_style_only"
        )
        is True,
        "pr67_is_scope_boundary_not_runtime_consumer_authority": registry.get(
            "pr67_is_scope_boundary_not_runtime_consumer_authority"
        )
        is True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "agent_role_count_from_charter_registry": len(charters_by_role),
        "algorithm_family_count_from_algorithm_registry": len(algorithm_families),
        "binding_count_from_binding_registry": len(bindings),
        "expected_allowed_attempt_count_from_binding_registry": len(bindings),
        "actual_allowed_attempt_count": len(allowed),
        "missing_allowed_attempt_count": len(
            [key for key in expected_allowed_keys if key not in actual_allowed_keys]
        ),
        "unexpected_allowed_attempt_count": len(
            [key for key in actual_allowed_keys if key not in expected_allowed_keys]
        ),
        "blocked_attempt_count": len(blocked),
        "owner_override_attempt_count": len(owner_override),
        "invalid_agent_role_attempt_count": sum(
            1
            for attempt in allowed
            if attempt.get("agent_role") not in charters_by_role
        ),
        "invalid_algorithm_family_attempt_count": sum(
            1
            for attempt in allowed
            if attempt.get("algorithm_family_name") not in families_by_name
        ),
        "invalid_binding_attempt_count": sum(
            1
            for attempt in allowed
            if attempt.get("binding_id") not in bindings_by_id
        ),
        "invalid_consumer_class_authorization_count": sum(
            1
            for attempt in allowed
            if attempt.get("requested_consumer_class")
            not in _string_list(
                bindings_by_id.get(str(attempt.get("binding_id")), {}).get(
                    "authorized_consumer_classes"
                )
            )
        ),
        "invalid_trade_context_authorization_count": sum(
            1
            for attempt in allowed
            if attempt.get("requested_trade_context")
            not in _string_list(
                bindings_by_id.get(str(attempt.get("binding_id")), {}).get(
                    "trade_context_applicability"
                )
            )
        ),
        "attempts_with_duplicate_id_count": duplicate_id_count,
        "allowed_attempts_with_owner_override_count": sum(
            1 for attempt in allowed if attempt.get("owner_override_present") is True
        ),
        "blocked_attempts_with_owner_override_count": sum(
            1 for attempt in blocked if attempt.get("owner_override_present") is True
        ),
        "owner_override_attempts_without_satisfaction_count": sum(
            1
            for attempt in owner_override
            if attempt.get("owner_override_satisfaction_result")
            != "OWNER_OVERRIDE_SATISFIED"
        ),
        "owner_override_attempts_fabricating_binding_rows_count": sum(
            1
            for attempt in owner_override
            if attempt.get("binding_row_fabricated_by_owner_override") is True
        ),
        "missing_binding_block_covered": any(
            attempt.get("attempt_type") == "BLOCKED_MISSING_BINDING"
            for attempt in attempts
        ),
        "unauthorized_consumer_class_block_covered": any(
            attempt.get("attempt_type") == "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS"
            for attempt in attempts
        ),
        "unauthorized_trade_context_block_covered": any(
            attempt.get("attempt_type") == "BLOCKED_UNAUTHORIZED_TRADE_CONTEXT"
            for attempt in attempts
        ),
        "owner_override_missing_binding_covered": any(
            attempt.get("attempt_type") == "OWNER_OVERRIDE_MISSING_BINDING"
            for attempt in attempts
        ),
        "owner_override_unauthorized_consumer_class_covered": any(
            attempt.get("attempt_type")
            == "OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS"
            for attempt in attempts
        ),
        "owner_override_unauthorized_trade_context_covered": any(
            attempt.get("attempt_type")
            == "OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT"
            for attempt in attempts
        ),
        "quantum_forward_design_supported": registry.get(
            "quantum_forward_design_supported"
        )
        is True,
        "quantum_or_quantum_compatible_allowed_attempt_count": len(quantum_allowed),
        "quantum_allowed_attempts_with_owner_quantum_priority_supported_count": sum(
            1
            for attempt in quantum_allowed
            if attempt.get("owner_quantum_priority_supported") is True
        ),
        "quantum_allowed_attempts_with_owner_can_force_quantum_priority_count": sum(
            1
            for attempt in quantum_allowed
            if attempt.get("owner_can_force_quantum_priority") is True
        ),
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
        "static_agent_algorithm_consumer_gate_created": registry.get(
            "static_agent_algorithm_consumer_gate_created"
        )
        is True,
        "agent_algorithm_cumulative_readiness_gate_created": registry.get(
            "agent_algorithm_cumulative_readiness_gate_created"
        )
        is True,
        "agent_algorithm_command_matrix_created": registry.get(
            "agent_algorithm_command_matrix_created"
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
        "bundle_file_present": (repo_root / CANONICAL_BUNDLE).exists(),
        "bundle_sha_present": (repo_root / CANONICAL_BUNDLE_SHA).exists(),
        "uses_pr_number_as_authority": registry.get("uses_pr_number_as_authority")
        is True
        or _uses_pr_number_as_authority(registry),
        "final_ready": registry.get("final_ready") is True,
        "authority_boundary_all_false": authority_boundary_all_false,
    }


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("agent_algorithm_consumer_gate_report")
    if not isinstance(report_schema, dict):
        return ["schema report definition is missing"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_counts = {
        "agent_role_count_from_charter_registry": 25,
        "algorithm_family_count_from_algorithm_registry": 15,
        "missing_allowed_attempt_count": 0,
        "unexpected_allowed_attempt_count": 0,
        "invalid_agent_role_attempt_count": 0,
        "invalid_algorithm_family_attempt_count": 0,
        "invalid_binding_attempt_count": 0,
        "invalid_consumer_class_authorization_count": 0,
        "invalid_trade_context_authorization_count": 0,
        "attempts_with_duplicate_id_count": 0,
        "allowed_attempts_with_owner_override_count": 0,
        "blocked_attempts_with_owner_override_count": 0,
        "owner_override_attempts_without_satisfaction_count": 0,
        "owner_override_attempts_fabricating_binding_rows_count": 0,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    if report.get("binding_count_from_binding_registry") != report.get(
        "expected_allowed_attempt_count_from_binding_registry"
    ):
        failures.append("report binding count must equal expected allowed attempts")
    if report.get("actual_allowed_attempt_count") != report.get(
        "expected_allowed_attempt_count_from_binding_registry"
    ):
        failures.append("report actual allowed count must equal expected allowed count")
    for field, minimum in (
        ("blocked_attempt_count", 5),
        ("owner_override_attempt_count", 5),
    ):
        if report.get(field, 0) < minimum:
            failures.append(f"report.{field} must be at least {minimum}")
    for field in (
        "missing_binding_block_covered",
        "unauthorized_consumer_class_block_covered",
        "unauthorized_trade_context_block_covered",
        "owner_override_missing_binding_covered",
        "owner_override_unauthorized_consumer_class_covered",
        "owner_override_unauthorized_trade_context_covered",
        "deterministic_output",
        "master_plan_followed_as_controlling_doctrine",
        "agent_charter_registry_used_for_role_validation",
        "algorithm_formula_family_registry_used_for_family_validation",
        "agent_algorithm_binding_registry_used_for_binding_validation",
        "existing_pr_patterns_used_for_style_only",
        "pr67_is_scope_boundary_not_runtime_consumer_authority",
        "quantum_forward_design_supported",
        "static_agent_algorithm_consumer_gate_created",
        "authority_boundary_all_false",
    ):
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    for field in (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "agent_algorithm_cumulative_readiness_gate_created",
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
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    ):
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    quantum_count = report.get("quantum_or_quantum_compatible_allowed_attempt_count")
    if (
        report.get("quantum_allowed_attempts_with_owner_quantum_priority_supported_count")
        != quantum_count
    ):
        failures.append(
            "report quantum owner-priority count must equal quantum allowed count"
        )
    if (
        report.get("quantum_allowed_attempts_with_owner_can_force_quantum_priority_count")
        != quantum_count
    ):
        failures.append(
            "report quantum owner-forced count must equal quantum allowed count"
        )
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must use deterministic sentinel")
    if report.get("source_of_gate_substance") != SOURCE_OF_GATE_SUBSTANCE:
        failures.append("report.source_of_gate_substance must point to master plan")
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
    agent_registry_path: pathlib.Path,
    algorithm_registry_path: pathlib.Path,
    binding_registry_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    registry, registry_failures = _load_registry(root / registry_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    agent_registry, agent_registry_failures = _load_registry(root / agent_registry_path)
    algorithm_registry, algorithm_registry_failures = _load_registry(
        root / algorithm_registry_path
    )
    binding_registry, binding_registry_failures = _load_registry(
        root / binding_registry_path
    )
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    failures.extend(agent_registry_failures)
    failures.extend(algorithm_registry_failures)
    failures.extend(binding_registry_failures)

    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    families_by_name, algorithm_families, family_failures = _algorithm_families_by_name(
        algorithm_registry
    )
    bindings_by_id, bindings, binding_failures = _bindings_by_id(binding_registry)
    failures.extend(charter_failures)
    failures.extend(family_failures)
    failures.extend(binding_failures)

    agent_roles = list(charters_by_role)
    agent_role_ids = [
        str(charters_by_role[role].get("agent_role_id", "")) for role in agent_roles
    ]
    algorithm_family_names = [
        str(family.get("algorithm_family_name", "")) for family in algorithm_families
    ]
    algorithm_family_ids = [
        str(family.get("algorithm_family_id", "")) for family in algorithm_families
    ]

    if schema is not None:
        failures.extend(
            _validate_schema_surface(
                schema,
                agent_roles=agent_roles,
                agent_role_ids=agent_role_ids,
                algorithm_family_names=algorithm_family_names,
                algorithm_family_ids=algorithm_family_ids,
            )
        )
    if registry is not None:
        failures.extend(_validate_top_level(registry, label="registry", schema=schema))
        failures.extend(
            _validate_attempts(
                value=registry,
                label="registry",
                strict_full_registry=True,
                charters_by_role=charters_by_role,
                families_by_name=families_by_name,
                bindings_by_id=bindings_by_id,
                bindings=bindings,
            )
        )
    if fixture is not None:
        failures.extend(_validate_top_level(fixture, label="fixture", schema=schema))
        failures.extend(
            _validate_attempts(
                value=fixture,
                label="fixture",
                strict_full_registry=False,
                charters_by_role=charters_by_role,
                families_by_name=families_by_name,
                bindings_by_id=bindings_by_id,
                bindings=bindings,
            )
        )

    failures.extend(
        validate_current_atomicrows_bundle_state(
            root,
            label="QTT agent algorithm consumer gate",
        )
    )
    failures.extend(binding_gate._master_plan_has_no_diff(root))

    report = build_report(
        registry or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        binding_registry=binding_registry or {},
        repo_root=root,
    )
    second_report = build_report(
        registry or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        binding_registry=binding_registry or {},
        repo_root=root,
    )
    if report != second_report:
        failures.append("generated agent-algorithm consumer gate report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: static agent-algorithm consumer gate is not "
            "a cumulative readiness gate or command matrix"
        )

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    agent_registry = load_registry(root / AGENT_CHARTER_REGISTRY)
    algorithm_registry = load_registry(root / ALGORITHM_FORMULA_FAMILY_REGISTRY)
    binding_registry = load_registry(root / AGENT_ALGORITHM_BINDING_REGISTRY)
    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    _, algorithm_families, family_failures = _algorithm_families_by_name(
        algorithm_registry
    )
    if charter_failures or family_failures:
        raise ValueError("; ".join([*charter_failures, *family_failures]))
    agent_roles = list(charters_by_role)
    agent_role_ids = [
        str(charters_by_role[role].get("agent_role_id", "")) for role in agent_roles
    ]
    algorithm_family_names = [
        str(family.get("algorithm_family_name", "")) for family in algorithm_families
    ]
    algorithm_family_ids = [
        str(family.get("algorithm_family_id", "")) for family in algorithm_families
    ]
    registry = build_registry_from_dependencies(
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        synthetic=False,
    )
    fixture = build_registry_from_dependencies(
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        synthetic=True,
    )
    schema = build_schema(
        agent_roles=agent_roles,
        agent_role_ids=agent_role_ids,
        algorithm_family_names=algorithm_family_names,
        algorithm_family_ids=algorithm_family_ids,
    )
    report = build_report(
        registry,
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
        binding_registry=binding_registry,
        repo_root=root,
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
    parser.add_argument("--agent-registry", default=str(AGENT_CHARTER_REGISTRY))
    parser.add_argument(
        "--algorithm-registry",
        default=str(ALGORITHM_FORMULA_FAMILY_REGISTRY),
    )
    parser.add_argument(
        "--binding-registry",
        default=str(AGENT_ALGORITHM_BINDING_REGISTRY),
    )
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
        agent_registry_path=pathlib.Path(args.agent_registry),
        algorithm_registry_path=pathlib.Path(args.algorithm_registry),
        binding_registry_path=pathlib.Path(args.binding_registry),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"allowed={report.get('actual_allowed_attempt_count', 0)} "
            f"blocked={report.get('blocked_attempt_count', 0)} "
            f"owner_override={report.get('owner_override_attempt_count', 0)} "
            f"quantum_or_compatible="
            f"{report.get('quantum_or_quantum_compatible_allowed_attempt_count', 0)} "
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
