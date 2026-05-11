#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Sequence

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
    pathlib.Path("schemas")
    / "agent_algorithm"
    / "qtt_agent_algorithm_binding_registry.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agent_algorithm"
    / "QTTAgentAlgorithmBindingRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "agent_algorithm"
    / "synthetic_qtt_agent_algorithm_binding_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentAlgorithmBindingReport.json"
)
AGENT_CHARTER_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agents"
    / "QTTAgentRoleOperatingCharterRegistry.yaml"
)
ALGORITHM_FORMULA_FAMILY_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "algorithms"
    / "QTTAlgorithmFormulaFamilyRegistry.yaml"
)
MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REGISTRY_TYPE = "QTT_AGENT_ALGORITHM_BINDING_REGISTRY"
REGISTRY_VERSION = "v1"
REPORT_TYPE = "QTT_AGENT_ALGORITHM_BINDING_REPORT"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
SOURCE_OF_BINDING_SUBSTANCE = MASTER_PLAN.as_posix()
BINDING_GENERATION_POLICY = (
    "ONE_BINDING_PER_ALGORITHM_AUTHORIZED_AGENT_ROLE_PAIR_FROM_ALGORITHM_REGISTRY"
)
ARCHITECTURE_EMPHASIS = (
    "INSTITUTIONAL_AGENT_ALGORITHM_BINDING_REGISTRY_NOT_LOOSE_LIST"
)
OWNER_OVERRIDE_SATISFACTION_BASIS = (
    "OWNER_GLOBAL_OVERRIDE_SATISFIES_QTT_INTERNAL_WORKFLOW_REQUIREMENTS"
)
STATIC_FORWARD_REFERENCE_ONLY = "STATIC_FORWARD_REFERENCE_ONLY"
BINDING_AUTHORITY_CLASS = (
    "MASTER_PLAN_AND_CANONICAL_REGISTRY_DERIVED_STATIC_AGENT_ALGORITHM_BINDING"
)
BINDING_STATUS = "ACTIVE_STATIC_AGENT_ALGORITHM_BINDING"
FINAL_STATUS = (
    "STATIC_AGENT_ALGORITHM_BINDING_DECLARED_NOT_FINAL_PRODUCTION_READY_OWNER_OVERRIDE_SUPPORTED"
)
SUCCESS_MARKER = "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK"
FAILURE_MARKER = "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_FAILED"
FINAL_INCOMPLETE_MARKER = "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_FINAL_INCOMPLETE"

TOP_FIELDS = (
    "registry_type",
    "registry_version",
    "deterministic_output",
    "generated_at_utc",
    "source_of_binding_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "binding_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "algorithm_formula_family_registry_used_for_family_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr66_is_scope_boundary_not_binding_authority",
    "architecture_emphasis",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "missing_binding_owner_override_supported",
    "owner_override_satisfies_missing_binding_for_internal_workflow",
    "normal_missing_binding_blocks_consumption_without_owner_override",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "static_agent_algorithm_binding_registry_created",
    "agent_algorithm_consumer_gate_created",
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
    "agent_algorithm_bindings",
)

FIXTURE_EXTRA_FIELDS = (
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "mode",
    "execution",
)

BINDING_FIELDS = (
    "binding_id",
    "binding_status",
    "binding_authority_class",
    "agent_role",
    "agent_role_id",
    "algorithm_family_name",
    "algorithm_family_id",
    "family_category",
    "classical_or_quantum",
    "formula_class",
    "formula_expression_profile",
    "authorized_consumer_classes",
    "trade_context_applicability",
    "latency_class",
    "risk_class",
    "capital_class",
    "input_parameter_families",
    "output_signal_type",
    "output_artifact_types",
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
    "runtime_live_order_authority_created",
    "direct_order_submission_allowed",
    "execution_router_required_for_live_order_path",
    "agent_binding_required_before_consumption",
    "consumer_gate_required_before_consumption",
    "source_evidence_requirement_class",
    "connector_requirement_class",
    "runtime_resolver_requirement_class",
    "replay_paper_requirement_class",
    "risk_gate_requirement_class",
    "sizing_gate_requirement_class",
    "latency_gate_requirement_class",
    "validation_gate_requirement_class",
    "owner_override_supported",
    "owner_override_satisfaction_basis",
    "missing_binding_owner_override_supported",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
    "blocks_qtt_when_owner_override_present",
    "agent_charter_reference",
    "algorithm_family_reference",
    "master_plan_doctrine_terms_used",
    "binding_derivation_summary",
    "final_qtt_internal_status",
)

ARRAY_FIELDS = {
    "authorized_consumer_classes",
    "trade_context_applicability",
    "input_parameter_families",
    "output_artifact_types",
    "optimizer_compatibility",
    "quantum_applicability",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "master_plan_doctrine_terms_used",
}

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_binding_substance",
    "agent_charter_registry_dependency",
    "algorithm_formula_family_registry_dependency",
    "binding_generation_policy",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "algorithm_formula_family_registry_used_for_family_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr66_is_scope_boundary_not_binding_authority",
    "architecture_emphasis",
    "agent_role_count_from_charter_registry",
    "algorithm_family_count_from_algorithm_registry",
    "expected_binding_count_from_algorithm_registry_authorized_roles",
    "actual_binding_count",
    "missing_binding_count",
    "unexpected_binding_count",
    "duplicate_binding_id_count",
    "invalid_agent_role_count",
    "invalid_algorithm_family_count",
    "invalid_agent_role_id_count",
    "invalid_algorithm_family_id_count",
    "algorithm_families_with_at_least_one_binding_count",
    "required_roadmap_example_binding_count",
    "required_roadmap_example_bindings_present_count",
    "bindings_with_owner_override_supported_count",
    "bindings_block_owner_override_count",
    "bindings_with_missing_binding_owner_override_supported_count",
    "bindings_with_consumer_gate_required_count",
    "quantum_forward_design_supported",
    "quantum_or_quantum_compatible_binding_count",
    "quantum_bindings_with_owner_quantum_priority_supported_count",
    "quantum_bindings_with_owner_can_force_quantum_priority_count",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_evidence_claim_created",
    "static_agent_algorithm_binding_registry_created",
    "agent_algorithm_consumer_gate_created",
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

TOP_CONST_EXPECTATIONS = {
    "registry_type": REGISTRY_TYPE,
    "registry_version": REGISTRY_VERSION,
    "deterministic_output": True,
    "generated_at_utc": DETERMINISTIC_GENERATED_AT,
    "source_of_binding_substance": SOURCE_OF_BINDING_SUBSTANCE,
    "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
    "algorithm_formula_family_registry_dependency": (
        ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
    ),
    "binding_generation_policy": BINDING_GENERATION_POLICY,
    "master_plan_followed_as_controlling_doctrine": True,
    "agent_charter_registry_used_for_role_validation": True,
    "algorithm_formula_family_registry_used_for_family_validation": True,
    "existing_pr_patterns_used_for_style_only": True,
    "pr66_is_scope_boundary_not_binding_authority": True,
    "architecture_emphasis": ARCHITECTURE_EMPHASIS,
    "owner_global_override_authority": True,
    "owner_override_satisfies_all_qtt_internal_requirements": True,
    "missing_binding_owner_override_supported": True,
    "owner_override_satisfies_missing_binding_for_internal_workflow": True,
    "normal_missing_binding_blocks_consumption_without_owner_override": True,
    "chatgpt_authority_over_owner": False,
    "codex_authority_over_owner": False,
    "qtt_agent_authority_over_owner": False,
    "quantum_forward_design_supported": True,
    "quantum_evidence_claim_created": False,
    "alpha_evidence_claim_created": False,
    "profit_evidence_claim_created": False,
    "latency_superiority_evidence_claim_created": False,
    "execution_superiority_evidence_claim_created": False,
    "static_agent_algorithm_binding_registry_created": True,
    "agent_algorithm_consumer_gate_created": False,
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
}

FALSE_TOP_FLAGS = tuple(
    field for field, expected in TOP_CONST_EXPECTATIONS.items() if expected is False
)

AUTHORITY_FALSE_FIELDS = (
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "agent_algorithm_consumer_gate_created",
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

REQUIRED_ROADMAP_EXAMPLE_BINDINGS = (
    ("OPTIMIZER_AGENT", "CLASSICAL_SCORING_ALGORITHM"),
    ("OPTIMIZER_AGENT", "QUBO_COMPATIBLE_ALGORITHM"),
    ("QUANTUM_RESEARCH_AGENT", "QAOA_COMPATIBLE_ALGORITHM"),
    ("RISK_AGENT", "CLASSICAL_RISK_ALGORITHM"),
    ("EXECUTION_LATENCY_AGENT", "CLASSICAL_LATENCY_ALGORITHM"),
)

QUANTUM_CLASS_VALUES = {
    "TRUE_QUANTUM",
    "QUANTUM_INSPIRED",
    "HYBRID_CLASSICAL_QUANTUM",
    "TRUE_QUANTUM_OR_QUANTUM_INSPIRED_COMPATIBLE",
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


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError(f"registry must contain an object: {path}")
        return value
    return load_yaml_subset(path)


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
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(f"{label}.{field}[{index}] must be an object")
            continue
        result.append(item)
    return result, failures


def _agent_charters_by_role(
    registry: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    charters, failures = _registry_items(registry, "agent_charters", "agent registry")
    by_role: dict[str, dict[str, Any]] = {}
    for index, charter in enumerate(charters):
        role = charter.get("agent_role")
        if not isinstance(role, str) or not role:
            failures.append(f"agent registry.agent_charters[{index}].agent_role is invalid")
            continue
        if role in by_role:
            failures.append(f"agent registry duplicate agent_role {role}")
        by_role[role] = charter
    return by_role, failures


def _algorithm_families_by_name(
    registry: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[str]]:
    families, failures = _registry_items(
        registry,
        "algorithm_families",
        "algorithm registry",
    )
    by_name: dict[str, dict[str, Any]] = {}
    for index, family in enumerate(families):
        name = family.get("algorithm_family_name")
        if not isinstance(name, str) or not name:
            failures.append(
                f"algorithm registry.algorithm_families[{index}].algorithm_family_name is invalid"
            )
            continue
        if name in by_name:
            failures.append(f"algorithm registry duplicate algorithm_family_name {name}")
        by_name[name] = family
    return by_name, families, failures


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _required_string(value: Any, default: str = STATIC_FORWARD_REFERENCE_ONLY) -> str:
    return value if isinstance(value, str) and value else default


def _family_is_quantum_or_compatible(family: dict[str, Any]) -> bool:
    return str(family.get("classical_or_quantum", "")) in QUANTUM_CLASS_VALUES


def _binding_pair(binding: dict[str, Any]) -> tuple[str, str]:
    return (
        str(binding.get("algorithm_family_name")),
        str(binding.get("agent_role")),
    )


def expected_binding_pairs(
    algorithm_families: Sequence[dict[str, Any]],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for family in algorithm_families:
        family_name = family.get("algorithm_family_name")
        roles = family.get("authorized_agent_roles")
        if not isinstance(family_name, str) or not isinstance(roles, list):
            continue
        for role in roles:
            if isinstance(role, str):
                pairs.append((family_name, role))
    return pairs


def binding_id_for(
    index: int,
    *,
    agent_role: str,
    algorithm_family_name: str,
) -> str:
    return (
        f"QTT_AGENT_ALGORITHM_BINDING_{index:03d}_"
        f"{agent_role}__{algorithm_family_name}"
    )


def _build_binding(
    *,
    index: int,
    agent_role: str,
    agent_charter: dict[str, Any],
    family: dict[str, Any],
) -> dict[str, Any]:
    family_name = _required_string(family.get("algorithm_family_name"))
    family_id = _required_string(family.get("algorithm_family_id"))
    agent_role_id = _required_string(agent_charter.get("agent_role_id"))
    return {
        "binding_id": binding_id_for(
            index,
            agent_role=agent_role,
            algorithm_family_name=family_name,
        ),
        "binding_status": BINDING_STATUS,
        "binding_authority_class": BINDING_AUTHORITY_CLASS,
        "agent_role": agent_role,
        "agent_role_id": agent_role_id,
        "algorithm_family_name": family_name,
        "algorithm_family_id": family_id,
        "family_category": _required_string(family.get("family_category")),
        "classical_or_quantum": _required_string(family.get("classical_or_quantum")),
        "formula_class": _required_string(family.get("formula_class")),
        "formula_expression_profile": _required_string(
            family.get("formula_expression_profile")
        ),
        "authorized_consumer_classes": _string_list(
            family.get("authorized_consumer_classes")
        ),
        "trade_context_applicability": _string_list(
            family.get("trade_context_applicability")
        ),
        "latency_class": _required_string(family.get("latency_class")),
        "risk_class": _required_string(family.get("risk_class")),
        "capital_class": _required_string(family.get("capital_class")),
        "input_parameter_families": _string_list(
            family.get("input_parameter_families")
        ),
        "output_signal_type": _required_string(family.get("output_signal_type")),
        "output_artifact_types": _string_list(family.get("output_artifact_types")),
        "optimizer_compatibility": _string_list(family.get("optimizer_compatibility")),
        "quantum_applicability": _string_list(family.get("quantum_applicability")),
        "quantum_algorithm_family_access": _string_list(
            family.get("quantum_algorithm_family_access")
        ),
        "quantum_parameter_family_access": _string_list(
            family.get("quantum_parameter_family_access")
        ),
        "deterministic_selection_role": _required_string(
            family.get("deterministic_selection_role")
        ),
        "scoring_ranking_role": _required_string(family.get("scoring_ranking_role")),
        "quantum_classical_arbitration_role": _required_string(
            family.get("quantum_classical_arbitration_role")
        ),
        "strongest_classical_comparator_required": (
            family.get("strongest_classical_comparator_required") is True
        ),
        "fallback_bundle_required": family.get("fallback_bundle_required") is True,
        "replay_paper_evidence_required_before_advantage_claim": (
            family.get("replay_paper_evidence_required_before_advantage_claim") is True
        ),
        "live_evidence_required_before_profit_claim": (
            family.get("live_evidence_required_before_profit_claim") is True
        ),
        "runtime_live_order_authority_created": False,
        "direct_order_submission_allowed": False,
        "execution_router_required_for_live_order_path": (
            family.get("execution_router_required_for_live_order_path") is True
        ),
        "agent_binding_required_before_consumption": (
            family.get("agent_binding_required_before_consumption") is True
        ),
        "consumer_gate_required_before_consumption": (
            family.get("consumer_gate_required_before_consumption") is True
        ),
        "source_evidence_requirement_class": _required_string(
            family.get("source_evidence_requirement_class")
        ),
        "connector_requirement_class": _required_string(
            family.get("connector_requirement_class")
        ),
        "runtime_resolver_requirement_class": _required_string(
            family.get("runtime_resolver_requirement_class")
        ),
        "replay_paper_requirement_class": _required_string(
            family.get("replay_paper_requirement_class")
        ),
        "risk_gate_requirement_class": _required_string(
            family.get("risk_gate_requirement_class")
        ),
        "sizing_gate_requirement_class": _required_string(
            family.get("sizing_gate_requirement_class")
        ),
        "latency_gate_requirement_class": _required_string(
            family.get("latency_gate_requirement_class")
        ),
        "validation_gate_requirement_class": _required_string(
            family.get("validation_gate_requirement_class")
        ),
        "owner_override_supported": True,
        "owner_override_satisfaction_basis": OWNER_OVERRIDE_SATISFACTION_BASIS,
        "missing_binding_owner_override_supported": True,
        "owner_quantum_priority_supported": (
            family.get("owner_quantum_priority_supported") is True
        ),
        "owner_can_force_quantum_priority": (
            family.get("owner_can_force_quantum_priority") is True
        ),
        "blocks_qtt_when_owner_override_present": False,
        "agent_charter_reference": (
            f"{AGENT_CHARTER_REGISTRY.as_posix()}#{agent_role_id}"
        ),
        "algorithm_family_reference": (
            f"{ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()}#{family_id}"
        ),
        "master_plan_doctrine_terms_used": _string_list(
            family.get("master_plan_doctrine_terms_used")
        ),
        "binding_derivation_summary": (
            f"Derived from algorithm registry authorized_agent_roles: {agent_role} "
            f"is listed for {family_name}; agent_role_id {agent_role_id} is "
            "validated from the agent charter registry."
        ),
        "final_qtt_internal_status": FINAL_STATUS,
    }


def build_registry_from_dependencies(
    *,
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    synthetic: bool = False,
) -> dict[str, Any]:
    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    _, families, family_failures = _algorithm_families_by_name(algorithm_registry)
    if charter_failures or family_failures:
        failures = [*charter_failures, *family_failures]
        raise ValueError("; ".join(failures))

    bindings: list[dict[str, Any]] = []
    index = 1
    for family in families:
        roles = family.get("authorized_agent_roles")
        if not isinstance(roles, list):
            continue
        for role in roles:
            if not isinstance(role, str):
                continue
            agent_charter = charters_by_role.get(role)
            if agent_charter is None:
                agent_charter = {"agent_role_id": STATIC_FORWARD_REFERENCE_ONLY}
            bindings.append(
                _build_binding(
                    index=index,
                    agent_role=role,
                    agent_charter=agent_charter,
                    family=family,
                )
            )
            index += 1

    registry = {
        "registry_type": REGISTRY_TYPE,
        "registry_version": REGISTRY_VERSION,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_binding_substance": SOURCE_OF_BINDING_SUBSTANCE,
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "binding_generation_policy": BINDING_GENERATION_POLICY,
        "master_plan_followed_as_controlling_doctrine": True,
        "agent_charter_registry_used_for_role_validation": True,
        "algorithm_formula_family_registry_used_for_family_validation": True,
        "existing_pr_patterns_used_for_style_only": True,
        "pr66_is_scope_boundary_not_binding_authority": True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "owner_global_override_authority": True,
        "owner_override_satisfies_all_qtt_internal_requirements": True,
        "missing_binding_owner_override_supported": True,
        "owner_override_satisfies_missing_binding_for_internal_workflow": True,
        "normal_missing_binding_blocks_consumption_without_owner_override": True,
        "chatgpt_authority_over_owner": False,
        "codex_authority_over_owner": False,
        "qtt_agent_authority_over_owner": False,
        "quantum_forward_design_supported": True,
        "quantum_evidence_claim_created": False,
        "alpha_evidence_claim_created": False,
        "profit_evidence_claim_created": False,
        "latency_superiority_evidence_claim_created": False,
        "execution_superiority_evidence_claim_created": False,
        "static_agent_algorithm_binding_registry_created": True,
        "agent_algorithm_consumer_gate_created": False,
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
        "agent_algorithm_bindings": bindings,
    }
    if synthetic:
        registry.update(
            {
                "fixture_id": "synthetic_qtt_agent_algorithm_binding_registry_v1",
                "fixture_version": "v1",
                "fixture_authority_class": (
                    "SYNTHETIC_SCHEMA_VALIDATION_FIXTURE_NOT_RUNTIME_AUTHORITY"
                ),
                "mode": "SOURCE_REQUIRED",
                "execution": "DISABLED",
            }
        )
    return registry


def _schema_string_array() -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": 1,
        "items": {"type": "string", "minLength": 1},
    }


def _schema_nonempty_string() -> dict[str, Any]:
    return {"type": "string", "minLength": 1}


def build_schema(
    *,
    agent_roles: Sequence[str],
    agent_role_ids: Sequence[str],
    algorithm_family_names: Sequence[str],
    algorithm_family_ids: Sequence[str],
) -> dict[str, Any]:
    binding_properties: dict[str, Any] = {
        "binding_id": _schema_nonempty_string(),
        "binding_status": {"const": BINDING_STATUS},
        "binding_authority_class": {"const": BINDING_AUTHORITY_CLASS},
        "agent_role": {"$ref": "#/$defs/agent_role"},
        "agent_role_id": {"$ref": "#/$defs/agent_role_id"},
        "algorithm_family_name": {"$ref": "#/$defs/algorithm_family_name"},
        "algorithm_family_id": {"$ref": "#/$defs/algorithm_family_id"},
        "family_category": _schema_nonempty_string(),
        "classical_or_quantum": _schema_nonempty_string(),
        "formula_class": _schema_nonempty_string(),
        "formula_expression_profile": _schema_nonempty_string(),
        "authorized_consumer_classes": _schema_string_array(),
        "trade_context_applicability": _schema_string_array(),
        "latency_class": _schema_nonempty_string(),
        "risk_class": _schema_nonempty_string(),
        "capital_class": _schema_nonempty_string(),
        "input_parameter_families": _schema_string_array(),
        "output_signal_type": _schema_nonempty_string(),
        "output_artifact_types": _schema_string_array(),
        "optimizer_compatibility": _schema_string_array(),
        "quantum_applicability": _schema_string_array(),
        "quantum_algorithm_family_access": _schema_string_array(),
        "quantum_parameter_family_access": _schema_string_array(),
        "deterministic_selection_role": _schema_nonempty_string(),
        "scoring_ranking_role": _schema_nonempty_string(),
        "quantum_classical_arbitration_role": _schema_nonempty_string(),
        "strongest_classical_comparator_required": {"type": "boolean"},
        "fallback_bundle_required": {"type": "boolean"},
        "replay_paper_evidence_required_before_advantage_claim": {"const": True},
        "live_evidence_required_before_profit_claim": {"const": True},
        "runtime_live_order_authority_created": {"const": False},
        "direct_order_submission_allowed": {"const": False},
        "execution_router_required_for_live_order_path": {"const": True},
        "agent_binding_required_before_consumption": {"const": True},
        "consumer_gate_required_before_consumption": {"const": True},
        "source_evidence_requirement_class": _schema_nonempty_string(),
        "connector_requirement_class": _schema_nonempty_string(),
        "runtime_resolver_requirement_class": _schema_nonempty_string(),
        "replay_paper_requirement_class": _schema_nonempty_string(),
        "risk_gate_requirement_class": _schema_nonempty_string(),
        "sizing_gate_requirement_class": _schema_nonempty_string(),
        "latency_gate_requirement_class": _schema_nonempty_string(),
        "validation_gate_requirement_class": _schema_nonempty_string(),
        "owner_override_supported": {"const": True},
        "owner_override_satisfaction_basis": {"const": OWNER_OVERRIDE_SATISFACTION_BASIS},
        "missing_binding_owner_override_supported": {"const": True},
        "owner_quantum_priority_supported": {"type": "boolean"},
        "owner_can_force_quantum_priority": {"type": "boolean"},
        "blocks_qtt_when_owner_override_present": {"const": False},
        "agent_charter_reference": _schema_nonempty_string(),
        "algorithm_family_reference": _schema_nonempty_string(),
        "master_plan_doctrine_terms_used": _schema_string_array(),
        "binding_derivation_summary": _schema_nonempty_string(),
        "final_qtt_internal_status": {"const": FINAL_STATUS},
    }
    top_properties: dict[str, Any] = {
        "registry_type": {"const": REGISTRY_TYPE},
        "registry_version": {"const": REGISTRY_VERSION},
        "deterministic_output": {"const": True},
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "source_of_binding_substance": {"const": SOURCE_OF_BINDING_SUBSTANCE},
        "agent_charter_registry_dependency": {
            "const": AGENT_CHARTER_REGISTRY.as_posix()
        },
        "algorithm_formula_family_registry_dependency": {
            "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        },
        "binding_generation_policy": {"const": BINDING_GENERATION_POLICY},
        "master_plan_followed_as_controlling_doctrine": {"const": True},
        "agent_charter_registry_used_for_role_validation": {"const": True},
        "algorithm_formula_family_registry_used_for_family_validation": {"const": True},
        "existing_pr_patterns_used_for_style_only": {"const": True},
        "pr66_is_scope_boundary_not_binding_authority": {"const": True},
        "architecture_emphasis": {"const": ARCHITECTURE_EMPHASIS},
        "owner_global_override_authority": {"const": True},
        "owner_override_satisfies_all_qtt_internal_requirements": {"const": True},
        "missing_binding_owner_override_supported": {"const": True},
        "owner_override_satisfies_missing_binding_for_internal_workflow": {
            "const": True
        },
        "normal_missing_binding_blocks_consumption_without_owner_override": {
            "const": True
        },
        "chatgpt_authority_over_owner": {"const": False},
        "codex_authority_over_owner": {"const": False},
        "qtt_agent_authority_over_owner": {"const": False},
        "quantum_forward_design_supported": {"const": True},
        "quantum_evidence_claim_created": {"const": False},
        "alpha_evidence_claim_created": {"const": False},
        "profit_evidence_claim_created": {"const": False},
        "latency_superiority_evidence_claim_created": {"const": False},
        "execution_superiority_evidence_claim_created": {"const": False},
        "static_agent_algorithm_binding_registry_created": {"const": True},
        "agent_algorithm_consumer_gate_created": {"const": False},
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
        "agent_algorithm_bindings": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"$ref": "#/$defs/agent_algorithm_binding"},
        },
        "fixture_id": _schema_nonempty_string(),
        "fixture_version": {"const": "v1"},
        "fixture_authority_class": _schema_nonempty_string(),
        "mode": {"const": "SOURCE_REQUIRED"},
        "execution": {"const": "DISABLED"},
    }
    report_properties = {
        field: {"type": "integer"}
        for field in REPORT_FIELDS
        if field.endswith("_count")
        or field
        in {
            "agent_role_count_from_charter_registry",
            "algorithm_family_count_from_algorithm_registry",
            "expected_binding_count_from_algorithm_registry_authorized_roles",
            "actual_binding_count",
        }
    }
    for field in REPORT_FIELDS:
        if field in report_properties:
            continue
        if field == "report_type":
            report_properties[field] = {"const": REPORT_TYPE}
        elif field == "generated_at_utc":
            report_properties[field] = {"const": DETERMINISTIC_GENERATED_AT}
        elif field == "source_of_binding_substance":
            report_properties[field] = {"const": SOURCE_OF_BINDING_SUBSTANCE}
        elif field == "agent_charter_registry_dependency":
            report_properties[field] = {"const": AGENT_CHARTER_REGISTRY.as_posix()}
        elif field == "algorithm_formula_family_registry_dependency":
            report_properties[field] = {
                "const": ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
            }
        elif field == "binding_generation_policy":
            report_properties[field] = {"const": BINDING_GENERATION_POLICY}
        elif field == "architecture_emphasis":
            report_properties[field] = {"const": ARCHITECTURE_EMPHASIS}
        elif field in {
            "deterministic_output",
            "master_plan_followed_as_controlling_doctrine",
            "agent_charter_registry_used_for_role_validation",
            "algorithm_formula_family_registry_used_for_family_validation",
            "existing_pr_patterns_used_for_style_only",
            "pr66_is_scope_boundary_not_binding_authority",
            "quantum_forward_design_supported",
            "static_agent_algorithm_binding_registry_created",
            "authority_boundary_all_false",
        }:
            report_properties[field] = {"type": "boolean"}
        else:
            report_properties[field] = {"type": "boolean"}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://qtt.local/schemas/agent_algorithm/"
            "qtt_agent_algorithm_binding_registry.schema.json"
        ),
        "title": "QTT Agent Algorithm Binding Registry",
        "description": (
            "Static deterministic QTT agent-algorithm binding registry schema. "
            "It binds canonical agent roles to canonical algorithm/formula families "
            "without creating runtime, live, order, source-acceptance, connector, "
            "replay, paper, profit, or quantum-backend artifacts."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(TOP_FIELDS),
        "properties": top_properties,
        "$defs": {
            "agent_role": {"enum": list(agent_roles)},
            "agent_role_id": {"enum": list(agent_role_ids)},
            "algorithm_family_name": {"enum": list(algorithm_family_names)},
            "algorithm_family_id": {"enum": list(algorithm_family_ids)},
            "agent_algorithm_binding": {
                "type": "object",
                "additionalProperties": False,
                "required": list(BINDING_FIELDS),
                "properties": binding_properties,
            },
            "agent_algorithm_binding_report": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REPORT_FIELDS),
                "properties": report_properties,
            },
        },
    }


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
) -> list[str]:
    expected = set(expected_fields)
    failures: list[str] = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values
    return [value]


def _uses_pr_number_as_authority_values(value: Any) -> bool:
    for item in _walk_values(value):
        if isinstance(item, str) and PR_NUMBER_PATTERN.search(item):
            return True
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
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_FIELDS):
        failures.append("schema.required must match top-level registry fields")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    if defs.get("agent_role", {}).get("enum") != list(agent_roles):
        failures.append("schema.$defs.agent_role must follow agent charter registry order")
    if defs.get("agent_role_id", {}).get("enum") != list(agent_role_ids):
        failures.append("schema.$defs.agent_role_id must follow agent charter registry ids")
    if defs.get("algorithm_family_name", {}).get("enum") != list(algorithm_family_names):
        failures.append(
            "schema.$defs.algorithm_family_name must follow algorithm registry order"
        )
    if defs.get("algorithm_family_id", {}).get("enum") != list(algorithm_family_ids):
        failures.append(
            "schema.$defs.algorithm_family_id must follow algorithm registry ids"
        )
    binding_def = defs.get("agent_algorithm_binding")
    if not isinstance(binding_def, dict):
        failures.append("schema.$defs.agent_algorithm_binding must be an object")
    elif binding_def.get("required") != list(BINDING_FIELDS):
        failures.append("schema binding required fields must match binding fields")
    report_def = defs.get("agent_algorithm_binding_report")
    if not isinstance(report_def, dict):
        failures.append("schema.$defs.agent_algorithm_binding_report must be an object")
    elif report_def.get("required") != list(REPORT_FIELDS):
        failures.append("schema report required fields must match report fields")
    return failures


def _validate_top_level(
    value: dict[str, Any],
    *,
    label: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    expected_fields = (
        (*TOP_FIELDS, *FIXTURE_EXTRA_FIELDS) if label == "fixture" else TOP_FIELDS
    )
    failures = _require_exact_fields(value, expected_fields, label)
    for field, expected in TOP_CONST_EXPECTATIONS.items():
        if value.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")
    if label == "fixture":
        if value.get("fixture_version") != "v1":
            failures.append("fixture.fixture_version must be v1")
        if value.get("mode") != "SOURCE_REQUIRED":
            failures.append("fixture.mode must be SOURCE_REQUIRED")
        if value.get("execution") != "DISABLED":
            failures.append("fixture.execution must be DISABLED")
    if schema is not None:
        failures.extend(validate_json_schema_subset(value, schema))
    return failures


def _validate_binding_fields(binding: dict[str, Any], *, index: int) -> list[str]:
    label = f"agent_algorithm_bindings[{index}]"
    failures = _require_exact_fields(binding, BINDING_FIELDS, label)
    for field in ARRAY_FIELDS:
        value = binding.get(field)
        if not isinstance(value, list) or not value:
            failures.append(f"{label}.{field} must be a non-empty array")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            failures.append(f"{label}.{field} must contain only non-empty strings")
    for field in BINDING_FIELDS:
        if field in ARRAY_FIELDS or isinstance(binding.get(field), bool):
            continue
        value = binding.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{label}.{field} must be a non-empty string")
    if binding.get("binding_status") != BINDING_STATUS:
        failures.append(f"{label}.binding_status is invalid")
    if binding.get("binding_authority_class") != BINDING_AUTHORITY_CLASS:
        failures.append(f"{label}.binding_authority_class is invalid")
    if binding.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_supported must be true")
    if binding.get("owner_override_satisfaction_basis") != OWNER_OVERRIDE_SATISFACTION_BASIS:
        failures.append(f"{label}.owner_override_satisfaction_basis is invalid")
    if binding.get("missing_binding_owner_override_supported") is not True:
        failures.append(f"{label}.missing_binding_owner_override_supported must be true")
    if binding.get("blocks_qtt_when_owner_override_present") is not False:
        failures.append(
            f"{label}.blocks_qtt_when_owner_override_present must be false"
        )
    for field in (
        "runtime_live_order_authority_created",
        "direct_order_submission_allowed",
    ):
        if binding.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    for field in (
        "replay_paper_evidence_required_before_advantage_claim",
        "live_evidence_required_before_profit_claim",
        "execution_router_required_for_live_order_path",
        "agent_binding_required_before_consumption",
        "consumer_gate_required_before_consumption",
    ):
        if binding.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    if binding.get("final_qtt_internal_status") != FINAL_STATUS:
        failures.append(f"{label}.final_qtt_internal_status is invalid")
    return failures


def _validate_binding_cross_references(
    binding: dict[str, Any],
    *,
    index: int,
    charters_by_role: dict[str, dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[str]:
    label = f"agent_algorithm_bindings[{index}]"
    failures: list[str] = []
    role = binding.get("agent_role")
    family_name = binding.get("algorithm_family_name")
    agent_charter = charters_by_role.get(str(role))
    family = families_by_name.get(str(family_name))
    if agent_charter is None:
        failures.append(f"{label}.agent_role unknown: {role}")
    elif binding.get("agent_role_id") != agent_charter.get("agent_role_id"):
        failures.append(f"{label}.agent_role_id does not match agent charter registry")
    if family is None:
        failures.append(f"{label}.algorithm_family_name unknown: {family_name}")
        return failures
    if binding.get("algorithm_family_id") != family.get("algorithm_family_id"):
        failures.append(
            f"{label}.algorithm_family_id does not match algorithm family registry"
        )
    roles = family.get("authorized_agent_roles")
    if not isinstance(roles, list) or role not in roles:
        failures.append(
            f"{label}: {role} is not authorized for {family_name} by algorithm registry"
        )
    for field in (
        "family_category",
        "classical_or_quantum",
        "formula_class",
        "formula_expression_profile",
        "latency_class",
        "risk_class",
        "capital_class",
        "output_signal_type",
        "deterministic_selection_role",
        "scoring_ranking_role",
        "quantum_classical_arbitration_role",
        "source_evidence_requirement_class",
        "connector_requirement_class",
        "runtime_resolver_requirement_class",
        "replay_paper_requirement_class",
        "risk_gate_requirement_class",
        "sizing_gate_requirement_class",
        "latency_gate_requirement_class",
        "validation_gate_requirement_class",
    ):
        if binding.get(field) != family.get(field):
            failures.append(f"{label}.{field} must match algorithm family registry")
    for field in (
        "authorized_consumer_classes",
        "trade_context_applicability",
        "input_parameter_families",
        "output_artifact_types",
        "optimizer_compatibility",
        "quantum_applicability",
        "quantum_algorithm_family_access",
        "quantum_parameter_family_access",
        "master_plan_doctrine_terms_used",
    ):
        if binding.get(field) != family.get(field):
            failures.append(f"{label}.{field} must match algorithm family registry")
    for field in (
        "strongest_classical_comparator_required",
        "fallback_bundle_required",
        "replay_paper_evidence_required_before_advantage_claim",
        "live_evidence_required_before_profit_claim",
        "runtime_live_order_authority_created",
        "direct_order_submission_allowed",
        "execution_router_required_for_live_order_path",
        "agent_binding_required_before_consumption",
        "consumer_gate_required_before_consumption",
        "owner_quantum_priority_supported",
        "owner_can_force_quantum_priority",
    ):
        if binding.get(field) != family.get(field):
            if field in {
                "runtime_live_order_authority_created",
                "direct_order_submission_allowed",
            } and binding.get(field) is False and family.get(field) is False:
                continue
            failures.append(f"{label}.{field} must follow algorithm family registry")
    if _family_is_quantum_or_compatible(family):
        if binding.get("owner_quantum_priority_supported") is not True:
            failures.append(
                f"{label}.owner_quantum_priority_supported must be true for quantum binding"
            )
        if binding.get("owner_can_force_quantum_priority") is not True:
            failures.append(
                f"{label}.owner_can_force_quantum_priority must be true for quantum binding"
            )
    return failures


def _validate_bindings(
    value: dict[str, Any],
    *,
    label: str,
    charters_by_role: dict[str, dict[str, Any]],
    algorithm_families: Sequence[dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[str]:
    bindings = value.get("agent_algorithm_bindings")
    if not isinstance(bindings, list):
        return [f"{label}.agent_algorithm_bindings must be a list"]

    failures: list[str] = []
    expected_pairs = expected_binding_pairs(algorithm_families)
    actual_pairs = [_binding_pair(binding) for binding in bindings if isinstance(binding, dict)]
    if actual_pairs != expected_pairs:
        missing = sorted(set(expected_pairs) - set(actual_pairs))
        unexpected = sorted(set(actual_pairs) - set(expected_pairs))
        failures.append(
            f"{label}.agent_algorithm_bindings must exactly match algorithm registry "
            "authorized_agent_roles order"
        )
        if missing:
            failures.append(f"{label} missing binding pairs: {missing}")
        if unexpected:
            failures.append(f"{label} unexpected binding pairs: {unexpected}")

    binding_ids: list[str] = []
    for index, binding in enumerate(bindings, start=1):
        if not isinstance(binding, dict):
            failures.append(f"{label}.agent_algorithm_bindings[{index - 1}] must be an object")
            continue
        binding_ids.append(str(binding.get("binding_id")))
        failures.extend(_validate_binding_fields(binding, index=index - 1))
        failures.extend(
            _validate_binding_cross_references(
                binding,
                index=index - 1,
                charters_by_role=charters_by_role,
                families_by_name=families_by_name,
            )
        )
        expected_id = binding_id_for(
            index,
            agent_role=str(binding.get("agent_role")),
            algorithm_family_name=str(binding.get("algorithm_family_name")),
        )
        if binding.get("binding_id") != expected_id:
            failures.append(
                f"{label}.agent_algorithm_bindings[{index - 1}].binding_id must be {expected_id}"
            )
    if len(set(binding_ids)) != len(binding_ids):
        failures.append(f"{label}.agent_algorithm_bindings must have unique binding_id")
    families_with_bindings = {pair[0] for pair in actual_pairs}
    for family in algorithm_families:
        family_name = family.get("algorithm_family_name")
        if family_name not in families_with_bindings:
            failures.append(f"{label}.{family_name} has no binding")
    failures.extend(_validate_required_roadmap_examples(actual_pairs, families_by_name))
    return failures


def _validate_required_roadmap_examples(
    actual_pairs: Sequence[tuple[str, str]],
    families_by_name: dict[str, dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    actual_pair_set = set(actual_pairs)
    for role, family_name in REQUIRED_ROADMAP_EXAMPLE_BINDINGS:
        family = families_by_name.get(family_name)
        if family is None:
            failures.append(
                f"roadmap example {role}->{family_name} references unknown algorithm family"
            )
            continue
        roles = family.get("authorized_agent_roles")
        if not isinstance(roles, list) or role not in roles:
            failures.append(
                f"roadmap example {role}->{family_name} is not authorized by "
                "QTTAlgorithmFormulaFamilyRegistry.yaml"
            )
            continue
        if (family_name, role) not in actual_pair_set:
            failures.append(f"roadmap example binding missing: {role}->{family_name}")
    return failures


def _master_plan_has_no_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--", MASTER_PLAN.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [f"git diff for master plan failed: {completed.stderr.strip()}"]
    if completed.stdout.strip():
        return [f"{MASTER_PLAN.as_posix()} must have no diff"]
    return []


def _invalid_agent_role_count(
    bindings: Sequence[dict[str, Any]],
    charters_by_role: dict[str, dict[str, Any]],
) -> int:
    return sum(1 for binding in bindings if binding.get("agent_role") not in charters_by_role)


def _invalid_algorithm_family_count(
    bindings: Sequence[dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> int:
    return sum(
        1 for binding in bindings if binding.get("algorithm_family_name") not in families_by_name
    )


def _invalid_agent_role_id_count(
    bindings: Sequence[dict[str, Any]],
    charters_by_role: dict[str, dict[str, Any]],
) -> int:
    count = 0
    for binding in bindings:
        charter = charters_by_role.get(str(binding.get("agent_role")))
        if charter is None or binding.get("agent_role_id") != charter.get("agent_role_id"):
            count += 1
    return count


def _invalid_algorithm_family_id_count(
    bindings: Sequence[dict[str, Any]],
    families_by_name: dict[str, dict[str, Any]],
) -> int:
    count = 0
    for binding in bindings:
        family = families_by_name.get(str(binding.get("algorithm_family_name")))
        if family is None or binding.get("algorithm_family_id") != family.get(
            "algorithm_family_id"
        ):
            count += 1
    return count


def _authority_boundary_all_false(report: dict[str, Any]) -> bool:
    return all(report.get(field) is False for field in AUTHORITY_FALSE_FIELDS)


def build_report(
    registry: dict[str, Any],
    *,
    agent_registry: dict[str, Any],
    algorithm_registry: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    charters_by_role, _ = _agent_charters_by_role(agent_registry)
    families_by_name, algorithm_families, _ = _algorithm_families_by_name(
        algorithm_registry
    )
    agent_bindings = registry.get("agent_algorithm_bindings")
    bindings = [
        binding for binding in agent_bindings if isinstance(binding, dict)
    ] if isinstance(agent_bindings, list) else []
    expected_pairs = expected_binding_pairs(algorithm_families)
    actual_pairs = [_binding_pair(binding) for binding in bindings]
    expected_set = set(expected_pairs)
    actual_set = set(actual_pairs)
    binding_ids = [str(binding.get("binding_id")) for binding in bindings]
    quantum_binding_count = sum(
        1
        for binding in bindings
        if _family_is_quantum_or_compatible(
            families_by_name.get(str(binding.get("algorithm_family_name")), {})
        )
    )
    roadmap_present_count = sum(
        1
        for role, family_name in REQUIRED_ROADMAP_EXAMPLE_BINDINGS
        if (family_name, role) in actual_set
    )
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_binding_substance": SOURCE_OF_BINDING_SUBSTANCE,
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "algorithm_formula_family_registry_dependency": (
            ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
        ),
        "binding_generation_policy": BINDING_GENERATION_POLICY,
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
        "existing_pr_patterns_used_for_style_only": registry.get(
            "existing_pr_patterns_used_for_style_only"
        )
        is True,
        "pr66_is_scope_boundary_not_binding_authority": registry.get(
            "pr66_is_scope_boundary_not_binding_authority"
        )
        is True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "agent_role_count_from_charter_registry": len(charters_by_role),
        "algorithm_family_count_from_algorithm_registry": len(algorithm_families),
        "expected_binding_count_from_algorithm_registry_authorized_roles": len(
            expected_pairs
        ),
        "actual_binding_count": len(bindings),
        "missing_binding_count": len(expected_set - actual_set),
        "unexpected_binding_count": len(actual_set - expected_set),
        "duplicate_binding_id_count": len(binding_ids) - len(set(binding_ids)),
        "invalid_agent_role_count": _invalid_agent_role_count(
            bindings,
            charters_by_role,
        ),
        "invalid_algorithm_family_count": _invalid_algorithm_family_count(
            bindings,
            families_by_name,
        ),
        "invalid_agent_role_id_count": _invalid_agent_role_id_count(
            bindings,
            charters_by_role,
        ),
        "invalid_algorithm_family_id_count": _invalid_algorithm_family_id_count(
            bindings,
            families_by_name,
        ),
        "algorithm_families_with_at_least_one_binding_count": len(
            {pair[0] for pair in actual_pairs}
        ),
        "required_roadmap_example_binding_count": len(
            REQUIRED_ROADMAP_EXAMPLE_BINDINGS
        ),
        "required_roadmap_example_bindings_present_count": roadmap_present_count,
        "bindings_with_owner_override_supported_count": sum(
            1 for binding in bindings if binding.get("owner_override_supported") is True
        ),
        "bindings_block_owner_override_count": sum(
            1
            for binding in bindings
            if binding.get("blocks_qtt_when_owner_override_present") is True
        ),
        "bindings_with_missing_binding_owner_override_supported_count": sum(
            1
            for binding in bindings
            if binding.get("missing_binding_owner_override_supported") is True
        ),
        "bindings_with_consumer_gate_required_count": sum(
            1
            for binding in bindings
            if binding.get("consumer_gate_required_before_consumption") is True
        ),
        "quantum_forward_design_supported": registry.get(
            "quantum_forward_design_supported"
        )
        is True,
        "quantum_or_quantum_compatible_binding_count": quantum_binding_count,
        "quantum_bindings_with_owner_quantum_priority_supported_count": sum(
            1
            for binding in bindings
            if _family_is_quantum_or_compatible(
                families_by_name.get(str(binding.get("algorithm_family_name")), {})
            )
            and binding.get("owner_quantum_priority_supported") is True
        ),
        "quantum_bindings_with_owner_can_force_quantum_priority_count": sum(
            1
            for binding in bindings
            if _family_is_quantum_or_compatible(
                families_by_name.get(str(binding.get("algorithm_family_name")), {})
            )
            and binding.get("owner_can_force_quantum_priority") is True
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
        "static_agent_algorithm_binding_registry_created": registry.get(
            "static_agent_algorithm_binding_registry_created"
        )
        is True,
        "agent_algorithm_consumer_gate_created": registry.get(
            "agent_algorithm_consumer_gate_created"
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
        or _uses_pr_number_as_authority_values(registry),
        "final_ready": registry.get("final_ready") is True,
        "authority_boundary_all_false": False,
    }
    report["authority_boundary_all_false"] = _authority_boundary_all_false(report)
    return report


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("agent_algorithm_binding_report")
    if not isinstance(report_schema, dict):
        return ["schema report definition is missing"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_counts = {
        "agent_role_count_from_charter_registry": 25,
        "algorithm_family_count_from_algorithm_registry": 15,
        "missing_binding_count": 0,
        "unexpected_binding_count": 0,
        "duplicate_binding_id_count": 0,
        "invalid_agent_role_count": 0,
        "invalid_algorithm_family_count": 0,
        "invalid_agent_role_id_count": 0,
        "invalid_algorithm_family_id_count": 0,
        "algorithm_families_with_at_least_one_binding_count": 15,
        "required_roadmap_example_binding_count": len(
            REQUIRED_ROADMAP_EXAMPLE_BINDINGS
        ),
        "required_roadmap_example_bindings_present_count": len(
            REQUIRED_ROADMAP_EXAMPLE_BINDINGS
        ),
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    if report.get("actual_binding_count") != report.get(
        "expected_binding_count_from_algorithm_registry_authorized_roles"
    ):
        failures.append("report.actual_binding_count must equal expected binding count")
    actual_count = report.get("actual_binding_count")
    for field in (
        "bindings_with_owner_override_supported_count",
        "bindings_with_missing_binding_owner_override_supported_count",
        "bindings_with_consumer_gate_required_count",
    ):
        if report.get(field) != actual_count:
            failures.append(f"report.{field} must equal actual_binding_count")
    quantum_count = report.get("quantum_or_quantum_compatible_binding_count")
    if report.get("quantum_bindings_with_owner_quantum_priority_supported_count") != quantum_count:
        failures.append(
            "report.quantum_bindings_with_owner_quantum_priority_supported_count "
            "must equal quantum_or_quantum_compatible_binding_count"
        )
    if report.get("quantum_bindings_with_owner_can_force_quantum_priority_count") != quantum_count:
        failures.append(
            "report.quantum_bindings_with_owner_can_force_quantum_priority_count "
            "must equal quantum_or_quantum_compatible_binding_count"
        )
    true_fields = (
        "deterministic_output",
        "master_plan_followed_as_controlling_doctrine",
        "agent_charter_registry_used_for_role_validation",
        "algorithm_formula_family_registry_used_for_family_validation",
        "existing_pr_patterns_used_for_style_only",
        "pr66_is_scope_boundary_not_binding_authority",
        "quantum_forward_design_supported",
        "static_agent_algorithm_binding_registry_created",
        "authority_boundary_all_false",
    )
    for field in true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    for field in AUTHORITY_FALSE_FIELDS:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must use deterministic sentinel")
    if report.get("source_of_binding_substance") != SOURCE_OF_BINDING_SUBSTANCE:
        failures.append("report.source_of_binding_substance must point to master plan")
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
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    failures.extend(agent_registry_failures)
    failures.extend(algorithm_registry_failures)

    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    families_by_name, algorithm_families, family_failures = _algorithm_families_by_name(
        algorithm_registry
    )
    failures.extend(charter_failures)
    failures.extend(family_failures)
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
            _validate_bindings(
                registry,
                label="registry",
                charters_by_role=charters_by_role,
                algorithm_families=algorithm_families,
                families_by_name=families_by_name,
            )
        )
        if _uses_pr_number_as_authority_values(registry):
            failures.append("registry must not use a delivery label as authority")
    if fixture is not None:
        failures.extend(_validate_top_level(fixture, label="fixture", schema=schema))
        failures.extend(
            _validate_bindings(
                fixture,
                label="fixture",
                charters_by_role=charters_by_role,
                algorithm_families=algorithm_families,
                families_by_name=families_by_name,
            )
        )
        if _uses_pr_number_as_authority_values(fixture):
            failures.append("fixture must not use a delivery label as authority")

    if (root / CANONICAL_BUNDLE).exists():
        failures.append("AtomicRows.bundle.jsonl must be absent")
    if (root / CANONICAL_BUNDLE_SHA).exists():
        failures.append("AtomicRows.bundle.sha256 must be absent")
    failures.extend(_master_plan_has_no_diff(root))

    report = build_report(
        registry or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        repo_root=root,
    )
    second_report = build_report(
        registry or {},
        agent_registry=agent_registry or {},
        algorithm_registry=algorithm_registry or {},
        repo_root=root,
    )
    if report != second_report:
        failures.append("generated agent-algorithm binding report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: static agent-algorithm binding registry is "
            "not a consumer gate or production-ready workflow"
        )

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    agent_registry = load_registry(root / AGENT_CHARTER_REGISTRY)
    algorithm_registry = load_registry(root / ALGORITHM_FORMULA_FAMILY_REGISTRY)
    charters_by_role, charter_failures = _agent_charters_by_role(agent_registry)
    _, algorithm_families, family_failures = _algorithm_families_by_name(
        algorithm_registry
    )
    if charter_failures or family_failures:
        failures = [*charter_failures, *family_failures]
        raise ValueError("; ".join(failures))
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
        synthetic=False,
    )
    fixture = build_registry_from_dependencies(
        agent_registry=agent_registry,
        algorithm_registry=algorithm_registry,
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
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"bindings={report.get('actual_binding_count', 0)} "
            f"expected="
            f"{report.get('expected_binding_count_from_algorithm_registry_authorized_roles', 0)} "
            f"quantum_or_compatible="
            f"{report.get('quantum_or_quantum_compatible_binding_count', 0)} "
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
