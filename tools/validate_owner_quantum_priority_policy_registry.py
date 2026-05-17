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
    pathlib.Path("schemas")
    / "quantum"
    / "owner_quantum_priority_policy_registry.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "OwnerQuantumPriorityPolicyRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "quantum"
    / "synthetic_owner_quantum_priority_policy_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerQuantumPriorityPolicyRegistry.report.json"
)

PR82_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "QuantumApplicabilityClassificationRegistry.yaml"
)
PR82_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QuantumApplicabilityClassificationRegistry.report.json"
)
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
PR76_SHORT_TEST = pathlib.Path(
    "tests/source_evidence/test_runtime_resolver_allowlist_live_blocks.py"
)
PR76_OLD_LONG_TEST = pathlib.Path(
    "tests/source_evidence/"
    "test_stage1_runtime_resolver_snapshot_consumer_allowlist_blocks_direct_live_dual_review_dashboard.py"
)

POLICY_REGISTRY_ID = "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY"
REPORT_ID = "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_REPORT"
POLICY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-QUANTUM-PRIORITY-POLICY"
POLICY_SCOPE = "STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY"
PR82_SEMANTIC_TASK_ID = "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
PR82_SUCCESS_MARKER = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
SUCCESS_MARKER = "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK"
FAILURE_MARKER = "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_FAILED"

MODE_ORDER = (
    "QUANTUM_NEUTRAL",
    "QUANTUM_PREFERRED",
    "QUANTUM_STRONGLY_PREFERRED",
    "QUANTUM_FIRST",
    "OWNER_FORCED_QUANTUM",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK",
)
PRIMARY_CLASS_ORDER = (
    "TRUE_QUANTUM",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUANTUM_INSPIRED",
    "CLASSICAL_ONLY",
)
LABEL_ORDER = (
    "TRUE_QUANTUM",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUANTUM_INSPIRED",
    "QUBO_COMPATIBLE",
    "ISING_COMPATIBLE",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
    "CLASSICAL_ONLY",
)
FUTURE_CONSUMER_CONTRACT_FIELDS = (
    "owner_priority_boost",
    "quantum_boost",
    "final_selection_score",
    "quantum_priority_applied",
    "owner_override_applied",
    "score_breakdown",
    "blocked_candidates",
    "reason_codes",
)
MODE_MULTIPLIERS = {
    "QUANTUM_NEUTRAL": (1.00, 1.00),
    "QUANTUM_PREFERRED": (1.10, 1.05),
    "QUANTUM_STRONGLY_PREFERRED": (1.25, 1.10),
    "QUANTUM_FIRST": (1.35, 1.15),
    "OWNER_FORCED_QUANTUM": (1.50, 1.20),
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK": (1.15, 1.05),
}
PRIORITY_MULTIPLIER_MIN = 1.00
PRIORITY_MULTIPLIER_MAX = 1.50
FAMILY_MULTIPLIER_MIN = 1.00
FAMILY_MULTIPLIER_MAX = 1.20

REASON_CODE_ORDER = (
    "OWNER_QUANTUM_PRIORITY_ALLOWED_METADATA_ONLY",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_NEUTRAL_MODE",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_PREFERRED_MODE",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_STRONGLY_PREFERRED_MODE",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_QUANTUM_FIRST_MODE",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_OWNER_FORCED_QUANTUM_INTERNAL_ONLY",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_HYBRID_TIEBREAK_INTERNAL_ONLY",
    "OWNER_QUANTUM_PRIORITY_ALLOWED_CLASSICAL_COMPARATOR",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_UNKNOWN_MODE",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_DUPLICATE_MODE",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_MISSING_REQUIRED_MODE",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_DEFAULT_MODE",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_SCORING_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_RANKING_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_SELECTION_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_REPLAY_PAPER_PROOF_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_RANDOM_POLICY_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
BLOCKED_POLICY_ORDER = (
    "UNKNOWN_QUANTUM_PRIORITY_MODE",
    "DUPLICATE_QUANTUM_PRIORITY_MODE",
    "MISSING_REQUIRED_QUANTUM_PRIORITY_MODE",
    "INVALID_DEFAULT_QUANTUM_PRIORITY_MODE",
    "INVALID_QUANTUM_PRIORITY_MULTIPLIER",
    "INVALID_PR82_APPLICABILITY_LABEL",
    "OWNER_FORCED_QUANTUM_WITHOUT_OWNER_BASIS",
    "OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "BACKEND_EXECUTION_CLAIM",
    "SIMULATOR_EXECUTION_CLAIM",
    "QAOA_EXECUTION_CLAIM",
    "VQE_EXECUTION_CLAIM",
    "ANNEALING_EXECUTION_CLAIM",
    "QUBO_SOLVE_CLAIM",
    "ISING_SOLVE_CLAIM",
    "OPTIMIZER_EXECUTION_CLAIM",
    "OPTIMIZER_ARBITRATION_CLAIM",
    "SCORING_EXECUTION_CLAIM",
    "RANKING_CLAIM",
    "SELECTION_CLAIM",
    "RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
    "SOURCE_ACCEPTANCE_CLAIM",
    "CONNECTOR_BINDING_CLAIM",
    "REPLAY_PAPER_PROOF_CLAIM",
    "QUANTUM_ADVANTAGE_CLAIM",
    "PROFIT_EVIDENCE_CLAIM",
    "LATENCY_SUPERIORITY_CLAIM",
    "EXECUTION_SUPERIORITY_CLAIM",
    "RANDOM_POLICY_ATTEMPT",
    "ATOMICROWS_BUNDLE_JSONL_CREATION",
    "ATOMICROWS_BUNDLE_SHA256_CREATION",
)
OWNER_OVERRIDE_BASES = (
    "NONE",
    "OWNER_APPROVED",
    "OWNER_APPROVED_OVERRIDE",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_OVERRIDE_SATISFIED",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
    "OWNER_APPROVED_NOT_EXTERNALLY_VERIFIED",
    "OWNER_APPROVED_UNVERIFIED",
    "OWNER_RISK_ACCEPTED",
    "OWNER_ASSUMED_RESPONSIBILITY",
    "OWNER_WAIVED_REQUIREMENT",
    "ROW_COMPLETION_OWNER_APPROVED",
)
OWNER_OVERRIDE_ACTIVE_BASES = tuple(base for base in OWNER_OVERRIDE_BASES if base != "NONE")

ROOT_TRUE_FIELDS = (
    "policy_is_metadata_only",
    "metadata_only_flag",
    "static_only_flag",
    "owner_quantum_priority_enabled",
    "quantum_tie_breaker_enabled",
    "owner_can_force_quantum_selection",
    "owner_override_applied",
    "owner_forced_quantum_internal_only",
    "classical_only_families_valid_as_comparators",
    "hybrid_compare_requires_classical_comparator",
    "future_scoring_policy_required",
    "future_stack_ranking_gate_required",
    "future_optimizer_arbitration_required",
    "future_candidate_stack_generation_required",
    "future_trade_context_stack_selection_required",
    "deterministic_policy_ordering",
)
ROOT_FALSE_FIELDS = (
    "owner_override_external_fact_fabrication_created",
    "owner_forced_quantum_bypasses_future_gates",
    "future_consumer_contract_execution_created",
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "optimizer_execution_created",
    "optimizer_arbitration_created",
    "scoring_execution_created",
    "ranking_created",
    "selection_created",
    "runtime_authority_created",
    "live_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_advantage_claim_created",
    "profit_evidence_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "random_policy_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "final_ready",
)
PR82_FALSE_FIELDS = (
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "optimizer_arbitration_created",
    "scoring_execution_created",
    "ranking_created",
    "selection_created",
    "quantum_advantage_claim_created",
    "profit_evidence_created",
)
DEPENDENCY_MARKERS = {
    "PR65_QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY": "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK",
    "PR66_QTT_AGENT_ALGORITHM_BINDING_REGISTRY": "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK",
    "PR67_QTT_AGENT_ALGORITHM_CONSUMER_GATE": "QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK",
    "PR68_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE": "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_OK",
    "PR73_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY": "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK",
    "PR74_ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE": "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK",
    "PR75_ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE": "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK",
    "PR77_EDGE_PARAMETER_STACK_SELECTION_PACKET": "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK",
    "PR78_QTT_TRADE_CONTEXT_PACKET": "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK",
    "PR79_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK",
    "PR80_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK",
    "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE": "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK",
    "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY": PR82_SUCCESS_MARKER,
}
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_REGISTRY_VALIDATES",
    "PASS_QUANTUM_NEUTRAL_METADATA_ONLY",
    "PASS_QUANTUM_PREFERRED_METADATA_ONLY",
    "PASS_QUANTUM_STRONGLY_PREFERRED_METADATA_ONLY",
    "PASS_QUANTUM_FIRST_METADATA_ONLY",
    "PASS_OWNER_FORCED_QUANTUM_INTERNAL_ONLY",
    "PASS_HYBRID_TIEBREAK_INTERNAL_ONLY",
    "PASS_CLASSICAL_COMPARATOR_VALID",
    "BLOCK_UNKNOWN_MODE",
    "BLOCK_DUPLICATE_MODE",
    "BLOCK_MISSING_REQUIRED_MODE",
    "BLOCK_INVALID_DEFAULT_MODE",
    "BLOCK_INVALID_MULTIPLIER",
    "BLOCK_INVALID_APPLICABILITY_LABEL",
    "BLOCK_OWNER_FORCED_WITHOUT_OWNER_BASIS",
    "BLOCK_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "BLOCK_BACKEND_EXECUTION",
    "BLOCK_SIMULATOR_EXECUTION",
    "BLOCK_OPTIMIZER_EXECUTION",
    "BLOCK_OPTIMIZER_ARBITRATION",
    "BLOCK_SCORING_EXECUTION",
    "BLOCK_RANKING",
    "BLOCK_SELECTION",
    "BLOCK_REPLAY_PAPER_PROOF",
    "BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY",
    "BLOCK_SOURCE_ACCEPTANCE",
    "BLOCK_CONNECTOR_SEMANTIC_BINDING",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "BLOCK_PROFIT_EVIDENCE",
    "BLOCK_LATENCY_SUPERIORITY_CLAIM",
    "BLOCK_EXECUTION_SUPERIORITY_CLAIM",
    "BLOCK_RANDOM_POLICY",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return value


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


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: registry file is missing: {path}"]
    try:
        return load_yaml(path), []
    except (OSError, ValueError, RegistryParseError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: registry file is invalid: {path}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label}{failure}" for failure in validate_json_schema_subset(payload, schema)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    index = {value: position for position, value in enumerate(order)}
    return sorted(dict.fromkeys(str(value) for value in values), key=lambda value: (index.get(value, 999), value))


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


def _mode_policy_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    policies = _list_of_mappings(payload.get("mode_policies"))
    return {str(policy.get("mode") or ""): policy for policy in policies}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _reason_code_for_false_field(field: str) -> str:
    field_map = {
        "backend_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_backend_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_simulator_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
        "qaoa_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
        "vqe_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_VQE_EXECUTION_FORBIDDEN",
        "annealing_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
        "qubo_solve_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_QUBO_SOLVE_FORBIDDEN",
        "ising_solve_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_ISING_SOLVE_FORBIDDEN",
        "optimizer_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
        "optimizer_arbitration_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
        "scoring_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SCORING_FORBIDDEN",
        "ranking_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_RANKING_FORBIDDEN",
        "selection_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SELECTION_FORBIDDEN",
        "runtime_authority_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "live_authority_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "order_authority_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "source_retrieval_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "source_acceptance_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "connector_semantic_binding_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
        "replay_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_REPLAY_PAPER_PROOF_FORBIDDEN",
        "paper_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_REPLAY_PAPER_PROOF_FORBIDDEN",
        "quantum_advantage_claim_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        "profit_evidence_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "latency_superiority_claim_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
        "execution_superiority_claim_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
        "owner_override_external_fact_fabrication_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
        "random_policy_used": "OWNER_QUANTUM_PRIORITY_BLOCKED_RANDOM_POLICY_FORBIDDEN",
        "atomicrows_bundle_jsonl_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
        "atomicrows_bundle_sha256_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
        "future_consumer_contract_execution_created": "OWNER_QUANTUM_PRIORITY_BLOCKED_SCORING_FORBIDDEN",
        "owner_forced_quantum_bypasses_future_gates": "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
        "final_ready": "OWNER_QUANTUM_PRIORITY_BLOCKED_SELECTION_FORBIDDEN",
    }
    return field_map.get(field, "OWNER_QUANTUM_PRIORITY_BLOCKED_UNKNOWN_MODE")


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependencies = _list_of_mappings(payload.get("depends_on_artifacts"))
    ids = [str(item.get("artifact_id") or "") for item in dependencies]
    if ids != sorted(DEPENDENCY_MARKERS):
        failures.append("depends_on_artifacts must list PR65-PR68, PR73-PR82 artifact IDs in deterministic order")
    for dependency in dependencies:
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is None:
            failures.append(f"unknown dependency artifact_id {artifact_id}")
            continue
        if dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id}.validation_marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            path_value = dependency.get(field)
            if not isinstance(path_value, str) or not path_value:
                failures.append(f"{artifact_id}.{field} must be a non-empty string")
                continue
            if not (repo_root / pathlib.Path(path_value)).exists():
                failures.append(f"{artifact_id}.{field} is missing: {path_value}")
        validator_path = dependency.get("validator_path")
        if isinstance(validator_path, str):
            validator_abs = repo_root / pathlib.Path(validator_path)
            if validator_abs.exists() and expected_marker not in validator_abs.read_text(encoding="utf-8"):
                failures.append(f"{artifact_id}.validator_path does not expose marker {expected_marker}")
    return failures


def validate_pr82_registry(repo_root: pathlib.Path) -> tuple[list[str], set[str], set[str]]:
    failures: list[str] = []
    registry, registry_failures = _load_yaml_checked(_resolve(repo_root, PR82_REGISTRY), "PR82_REGISTRY")
    report, report_failures = _load_json_checked(_resolve(repo_root, PR82_REPORT), "PR82_REPORT")
    failures.extend(registry_failures)
    failures.extend(report_failures)
    if registry is None or report is None:
        return failures, set(), set()

    if registry.get("semantic_task_id") != PR82_SEMANTIC_TASK_ID:
        failures.append(f"PR82_REGISTRY.semantic_task_id must be {PR82_SEMANTIC_TASK_ID}")
    if registry.get("classification_labels") != list(LABEL_ORDER):
        failures.append("PR82_REGISTRY.classification_labels must match canonical PR82 order")
    if registry.get("metadata_only_flag") is not True:
        failures.append("PR82_REGISTRY.metadata_only_flag must be true")
    if registry.get("classical_only_families_valid_as_comparators") is not True:
        failures.append("PR82_REGISTRY.classical_only_families_valid_as_comparators must be true")
    for field in PR82_FALSE_FIELDS:
        if registry.get(field) is not False:
            failures.append(f"PR82_REGISTRY.{field} must be false")
        if report.get(field) is not False:
            failures.append(f"PR82_REPORT.{field} must be false")
    if report.get("validation_marker") != PR82_SUCCESS_MARKER:
        failures.append(f"PR82_REPORT.validation_marker must be {PR82_SUCCESS_MARKER}")

    labels = set(str(label) for label in registry.get("classification_labels", []) if isinstance(label, str))
    primary_classes = set(PRIMARY_CLASS_ORDER)
    return failures, labels, primary_classes


def _validate_mode_policy(
    policy: dict[str, Any],
    *,
    expected_mode: str,
    known_labels: set[str],
    known_primary_classes: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    entry_label = f"{label}.{expected_mode}"
    if policy.get("mode") != expected_mode:
        failures.append(f"{entry_label}.mode must be {expected_mode}")
        return failures

    if policy.get("mode_enabled") is not True:
        failures.append(f"{entry_label}.mode_enabled must be true")
    if policy.get("owner_selectable") is not True:
        failures.append(f"{entry_label}.owner_selectable must be true")
    expected_owner_force = expected_mode == "OWNER_FORCED_QUANTUM"
    if policy.get("owner_can_force") is not expected_owner_force:
        failures.append(f"{entry_label}.owner_can_force must be {expected_owner_force}")
    if policy.get("metadata_only_flag") is not True:
        failures.append(f"{entry_label}.metadata_only_flag must be true")
    if policy.get("future_scoring_policy_required") is not True:
        failures.append(f"{entry_label}.future_scoring_policy_required must be true")
    if policy.get("future_optimizer_arbitration_required") is not True:
        failures.append(f"{entry_label}.future_optimizer_arbitration_required must be true")

    expected_priority, expected_family = MODE_MULTIPLIERS[expected_mode]
    priority = policy.get("priority_multiplier")
    family_multiplier = policy.get("quantum_applicable_family_multiplier")
    if not _is_number(priority) or not PRIORITY_MULTIPLIER_MIN <= float(priority) <= PRIORITY_MULTIPLIER_MAX:
        failures.append(f"OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: {entry_label}.priority_multiplier is out of bounds")
    elif float(priority) != expected_priority:
        failures.append(f"OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: {entry_label}.priority_multiplier must be {expected_priority:.2f}")
    if not _is_number(family_multiplier) or not FAMILY_MULTIPLIER_MIN <= float(family_multiplier) <= FAMILY_MULTIPLIER_MAX:
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: "
            f"{entry_label}.quantum_applicable_family_multiplier is out of bounds"
        )
    elif float(family_multiplier) != expected_family:
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: "
            f"{entry_label}.quantum_applicable_family_multiplier must be {expected_family:.2f}"
        )

    expected_tie_breaker = expected_mode != "QUANTUM_NEUTRAL"
    if policy.get("tie_breaker_enabled") is not expected_tie_breaker:
        failures.append(f"{entry_label}.tie_breaker_enabled must be {expected_tie_breaker}")
    expected_hybrid = expected_mode == "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK"
    if policy.get("hybrid_compare_required_before_quantum_preference") is not expected_hybrid:
        failures.append(f"{entry_label}.hybrid_compare_required_before_quantum_preference must be {expected_hybrid}")
    expected_comparator = expected_mode != "QUANTUM_NEUTRAL"
    if policy.get("classical_comparator_required") is not expected_comparator:
        failures.append(f"{entry_label}.classical_comparator_required must be {expected_comparator}")
    if expected_hybrid and policy.get("classical_comparator_required") is not True:
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL: "
            f"{entry_label} must require classical comparator metadata"
        )

    primary_classes = policy.get("allowed_primary_quantum_applicability_classes")
    if primary_classes != list(PRIMARY_CLASS_ORDER):
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL: "
            f"{entry_label}.allowed_primary_quantum_applicability_classes must match canonical order"
        )
    elif not set(primary_classes).issubset(known_primary_classes):
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL: "
            f"{entry_label}.allowed_primary_quantum_applicability_classes references unknown PR82 class"
        )

    labels = policy.get("allowed_applicability_labels")
    if labels != list(LABEL_ORDER):
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL: "
            f"{entry_label}.allowed_applicability_labels must match canonical PR82 order"
        )
    elif not set(labels).issubset(known_labels):
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL: "
            f"{entry_label}.allowed_applicability_labels references unknown PR82 label"
        )
    if isinstance(labels, list) and "CLASSICAL_ONLY" not in labels:
        failures.append(f"{entry_label}.allowed_applicability_labels must preserve CLASSICAL_ONLY comparator metadata")

    blocked_codes = policy.get("blocked_reason_codes")
    if blocked_codes != []:
        failures.append(f"{entry_label}.blocked_reason_codes must be empty for enabled modes")
    return failures


def validate_blocked_policies(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    blocked = _list_of_mappings(payload.get("blocked_policies"))
    blocked_ids = [str(item.get("mode_or_policy_id") or "") for item in blocked]
    if blocked_ids != list(BLOCKED_POLICY_ORDER):
        failures.append("blocked_policies must use deterministic canonical blocked policy order")
    if len(blocked) != len(BLOCK_REASON_CODES):
        failures.append("blocked_policies must cover each blocked reason code exactly once")
    for index, entry in enumerate(blocked):
        codes = entry.get("blocked_reason_codes")
        if not isinstance(codes, list) or not codes:
            failures.append(f"blocked_policies[{index}].blocked_reason_codes must be a non-empty list")
            continue
        unknown_codes = [str(code) for code in codes if str(code) not in REASON_CODE_ORDER]
        if unknown_codes:
            failures.append(f"blocked_policies[{index}].blocked_reason_codes has unknown codes {', '.join(unknown_codes)}")
        if [str(code) for code in codes] != _sort_reason_codes(str(code) for code in codes):
            failures.append(f"blocked_policies[{index}].blocked_reason_codes must use canonical deterministic order")
        if index < len(BLOCK_REASON_CODES) and codes != [BLOCK_REASON_CODES[index]]:
            failures.append(f"blocked_policies[{index}].blocked_reason_codes must be {[BLOCK_REASON_CODES[index]]}")
    return failures


def validate_policy_payload(
    payload: dict[str, Any],
    *,
    known_labels: set[str] | None = None,
    known_primary_classes: set[str] | None = None,
    label: str,
) -> list[str]:
    failures: list[str] = []
    known_labels = set(LABEL_ORDER) if known_labels is None else known_labels
    known_primary_classes = set(PRIMARY_CLASS_ORDER) if known_primary_classes is None else known_primary_classes

    if payload.get("policy_registry_id") != POLICY_REGISTRY_ID:
        failures.append(f"{label}.policy_registry_id must be {POLICY_REGISTRY_ID}")
    if payload.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"{label}.semantic_task_id must be {SEMANTIC_TASK_ID}")
    if payload.get("policy_scope") != POLICY_SCOPE:
        failures.append(f"{label}.policy_scope must be {POLICY_SCOPE}")
    if payload.get("policy_version") != POLICY_VERSION:
        failures.append(f"{label}.policy_version must be {POLICY_VERSION}")

    for field in ROOT_TRUE_FIELDS:
        if payload.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in ROOT_FALSE_FIELDS:
        if payload.get(field) is not False:
            code = _reason_code_for_false_field(field)
            failures.append(f"{code}: {label}.{field} must be false")

    for field in ("owner_quantum_priority_enabled", "owner_can_force_quantum_selection", "owner_override_applied"):
        if not isinstance(payload.get(field), bool):
            failures.append(f"{label}.{field} must be an explicit boolean")

    if payload.get("supported_quantum_priority_modes") != list(MODE_ORDER):
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_MISSING_REQUIRED_MODE: "
            f"{label}.supported_quantum_priority_modes must match canonical order"
        )
    reason_codes = payload.get("reason_codes")
    if reason_codes != list(REASON_CODE_ORDER):
        failures.append(f"{label}.reason_codes must match canonical deterministic order")
    if payload.get("future_consumer_contract_fields") != list(FUTURE_CONSUMER_CONTRACT_FIELDS):
        failures.append(f"{label}.future_consumer_contract_fields must match deterministic future consumer contract order")

    mode_policies = _list_of_mappings(payload.get("mode_policies"))
    mode_names = [str(policy.get("mode") or "") for policy in mode_policies]
    if mode_names != list(MODE_ORDER):
        missing = [mode for mode in MODE_ORDER if mode not in mode_names]
        unknown = [mode for mode in mode_names if mode not in MODE_ORDER]
        if missing:
            failures.append(
                "OWNER_QUANTUM_PRIORITY_BLOCKED_MISSING_REQUIRED_MODE: "
                f"{label}.mode_policies missing modes {', '.join(missing)}"
            )
        if unknown:
            failures.append(
                "OWNER_QUANTUM_PRIORITY_BLOCKED_UNKNOWN_MODE: "
                f"{label}.mode_policies unknown modes {', '.join(unknown)}"
            )
        if mode_names != _sort_by_order(mode_names, MODE_ORDER):
            failures.append(f"{label}.mode_policies must use canonical deterministic mode order")

    seen: set[str] = set()
    for mode in mode_names:
        if mode in seen:
            failures.append(
                "OWNER_QUANTUM_PRIORITY_BLOCKED_DUPLICATE_MODE: "
                f"{label}.mode_policies repeats mode {mode}"
            )
        seen.add(mode)

    policies_by_mode = _mode_policy_map(payload)
    for expected_mode in MODE_ORDER:
        policy = policies_by_mode.get(expected_mode)
        if policy is None:
            continue
        failures.extend(
            _validate_mode_policy(
                policy,
                expected_mode=expected_mode,
                known_labels=known_labels,
                known_primary_classes=known_primary_classes,
                label=label,
            )
        )

    default_mode = payload.get("default_quantum_priority_mode")
    if default_mode not in MODE_ORDER:
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_DEFAULT_MODE: "
            f"{label}.default_quantum_priority_mode must be supported"
        )
    elif payload.get("owner_quantum_priority_enabled") is True:
        supported = payload.get("supported_quantum_priority_modes")
        if isinstance(supported, list) and default_mode not in supported:
            failures.append(
                "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_DEFAULT_MODE: "
                f"{label}.default_quantum_priority_mode is not in supported modes"
            )
    if default_mode in policies_by_mode:
        default_policy = policies_by_mode[default_mode]
        if payload.get("quantum_priority_multiplier") != default_policy.get("priority_multiplier"):
            failures.append(f"{label}.quantum_priority_multiplier must match default mode priority multiplier")
        if payload.get("quantum_applicable_family_multiplier") != default_policy.get("quantum_applicable_family_multiplier"):
            failures.append(f"{label}.quantum_applicable_family_multiplier must match default mode family multiplier")

    basis = payload.get("owner_override_basis")
    if basis not in OWNER_OVERRIDE_BASES:
        failures.append(f"{label}.owner_override_basis is not allowed")
    if payload.get("owner_override_applied") is True and basis not in OWNER_OVERRIDE_ACTIVE_BASES:
        failures.append(f"{label}.owner_override_basis must be active when owner_override_applied is true")
    if default_mode == "OWNER_FORCED_QUANTUM" and basis not in OWNER_OVERRIDE_ACTIVE_BASES:
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS: "
            f"{label}.default OWNER_FORCED_QUANTUM requires owner_override_basis"
        )
    if payload.get("owner_can_force_quantum_selection") is True and basis not in OWNER_OVERRIDE_ACTIVE_BASES:
        failures.append(f"{label}.owner_can_force_quantum_selection requires an allowed owner basis")

    preferred = policies_by_mode.get("QUANTUM_PREFERRED", {})
    strongly = policies_by_mode.get("QUANTUM_STRONGLY_PREFERRED", {})
    first = policies_by_mode.get("QUANTUM_FIRST", {})
    forced = policies_by_mode.get("OWNER_FORCED_QUANTUM", {})
    if _is_number(strongly.get("priority_multiplier")) and _is_number(preferred.get("priority_multiplier")):
        if float(strongly["priority_multiplier"]) <= float(preferred["priority_multiplier"]):
            failures.append("OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: QUANTUM_STRONGLY_PREFERRED must exceed QUANTUM_PREFERRED")
    if _is_number(first.get("priority_multiplier")) and _is_number(strongly.get("priority_multiplier")):
        if float(first["priority_multiplier"]) < float(strongly["priority_multiplier"]):
            failures.append("OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: QUANTUM_FIRST must be >= QUANTUM_STRONGLY_PREFERRED")
    if _is_number(forced.get("priority_multiplier")) and _is_number(first.get("priority_multiplier")):
        if float(forced["priority_multiplier"]) < float(first["priority_multiplier"]):
            failures.append("OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER: OWNER_FORCED_QUANTUM must be >= QUANTUM_FIRST")

    hybrid = policies_by_mode.get("HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK", {})
    if hybrid.get("classical_comparator_required") is not True:
        failures.append("HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK must require classical_comparator_required=true")
    if hybrid.get("future_optimizer_arbitration_required") is not True:
        failures.append("HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK must require future optimizer arbitration")

    failures.extend(validate_blocked_policies(payload))
    return failures


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"fixture.semantic_task_id must be {SEMANTIC_TASK_ID}")
    if fixture.get("policy_scope") != POLICY_SCOPE:
        failures.append(f"fixture.policy_scope must be {POLICY_SCOPE}")
    for field in (
        "external_fact_authority_created",
        "runtime_authority_created",
        "live_authority_created",
        "order_authority_created",
        "source_retrieval_created",
        "source_acceptance_created",
        "connector_semantic_binding_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_solve_execution_created",
        "ising_solve_execution_created",
        "optimizer_execution_created",
        "optimizer_arbitration_created",
        "scoring_execution_created",
        "ranking_created",
        "selection_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_advantage_claim_created",
        "profit_evidence_created",
        "latency_superiority_claim_created",
        "execution_superiority_claim_created",
        "random_policy_used",
    ):
        if fixture.get(field) is not False:
            failures.append(f"fixture.{field} must be false")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id") or "") for case in cases]
    missing = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing:
        failures.append(f"fixture.fixture_cases missing case IDs {', '.join(missing)}")
    for case in cases:
        expected_code = case.get("expected_reason_code")
        if expected_code not in REASON_CODE_ORDER:
            failures.append(f"fixture case {case.get('case_id')} has unknown expected_reason_code")
        if case.get("synthetic_case_only") is not True:
            failures.append(f"fixture case {case.get('case_id')} must be synthetic_case_only")
    return failures


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (_resolve(repo_root, CANONICAL_BUNDLE_SHA256)).exists():
        failures.append(
            "OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    if not (_resolve(repo_root, PR76_SHORT_TEST)).exists():
        failures.append(f"PR76 short runtime resolver allowlist test is missing: {PR76_SHORT_TEST.as_posix()}")
    if (_resolve(repo_root, PR76_OLD_LONG_TEST)).exists():
        failures.append(f"old long runtime resolver allowlist filename must remain absent: {PR76_OLD_LONG_TEST.as_posix()}")
    return failures


def validate_master_plan_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--quiet", "--", MASTER_PLAN_CURRENT.as_posix()],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return [f"{MASTER_PLAN_CURRENT.as_posix()} has local diff; PR83 must not edit it"]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    text = validator_path.read_text(encoding="utf-8")
    forbidden_tokens = (
        "import " + "random",
        "from " + "random",
        "import " + "uuid",
        "from " + "uuid",
        "datetime" + ".now",
        "time" + ".time",
        "os" + ".environ",
        "requests" + ".",
        "urllib" + ".request",
        "http" + ".client",
        "socket" + ".",
    )
    return [f"validator contains forbidden nondeterministic or network token {token}" for token in forbidden_tokens if token in text]


def build_report(
    payload: dict[str, Any],
    pr82_labels: set[str],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    policies_by_mode = _mode_policy_map(payload)
    mode_policies = [copy.deepcopy(policies_by_mode[mode]) for mode in MODE_ORDER if mode in policies_by_mode]
    blocked_policies = copy.deepcopy(_list_of_mappings(payload.get("blocked_policies")))
    return {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "policy_registry_id": payload.get("policy_registry_id"),
        "semantic_task_id": payload.get("semantic_task_id"),
        "policy_scope": payload.get("policy_scope"),
        "policy_is_metadata_only": True,
        "metadata_only_flag": True,
        "static_only_flag": True,
        "owner_quantum_priority_enabled": payload.get("owner_quantum_priority_enabled"),
        "default_quantum_priority_mode": payload.get("default_quantum_priority_mode"),
        "supported_quantum_priority_modes": list(MODE_ORDER),
        "mode_policies": mode_policies,
        "blocked_policies": blocked_policies,
        "reason_codes": list(REASON_CODE_ORDER),
        "owner_can_force_quantum_selection": payload.get("owner_can_force_quantum_selection"),
        "owner_override_basis": payload.get("owner_override_basis"),
        "owner_override_applied": payload.get("owner_override_applied"),
        "owner_override_external_fact_fabrication_created": False,
        "owner_forced_quantum_internal_only": True,
        "owner_forced_quantum_bypasses_future_gates": False,
        "classical_only_families_valid_as_comparators": True,
        "hybrid_compare_requires_classical_comparator": True,
        "future_scoring_policy_required": True,
        "future_stack_ranking_gate_required": True,
        "future_optimizer_arbitration_required": True,
        "future_candidate_stack_generation_required": True,
        "future_trade_context_stack_selection_required": True,
        "future_consumer_contract_fields": list(FUTURE_CONSUMER_CONTRACT_FIELDS),
        "future_consumer_contract_execution_created": False,
        "pr82_quantum_applicability_registry_consumed": True,
        "pr82_semantic_task_id": PR82_SEMANTIC_TASK_ID,
        "pr82_applicability_labels": _sort_by_order(pr82_labels, LABEL_ORDER),
        "classical_only_label_validated_from_pr82": "CLASSICAL_ONLY" in pr82_labels,
        "backend_execution_created": False,
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_solve_execution_created": False,
        "ising_solve_execution_created": False,
        "optimizer_execution_created": False,
        "optimizer_arbitration_created": False,
        "scoring_execution_created": False,
        "ranking_created": False,
        "selection_created": False,
        "runtime_authority_created": False,
        "live_authority_created": False,
        "order_authority_created": False,
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "connector_semantic_binding_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "quantum_advantage_claim_created": False,
        "profit_evidence_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "random_policy_used": False,
        "deterministic_policy_ordering": True,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "final_ready": False,
    }


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    first = serialize_report(report)
    second = serialize_report(copy.deepcopy(report))
    if first != second:
        failures.append("generated report serialization is not byte-stable")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use the deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    for pattern in forbidden_patterns:
        if pattern.search(first):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    registry_path: pathlib.Path = DEFAULT_PRODUCTION_REGISTRY,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    registry_abs = _resolve(repo_root, registry_path)
    fixture_abs = _resolve(repo_root, fixture_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    registry, registry_failures = _load_yaml_checked(registry_abs, "REGISTRY")
    fixture, fixture_failures = _load_json_checked(fixture_abs, "FIXTURE")
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    if schema is None or registry is None or fixture is None:
        return ValidationResult(False, tuple(failures), None)

    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_fixture(fixture))
    pr82_failures, pr82_labels, pr82_primary_classes = validate_pr82_registry(repo_root)
    failures.extend(pr82_failures)
    failures.extend(validate_dependencies(registry, repo_root))
    failures.extend(
        validate_policy_payload(
            registry,
            known_labels=pr82_labels,
            known_primary_classes=pr82_primary_classes,
            label="REGISTRY",
        )
    )
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(registry, pr82_labels, repo_root)
    failures.extend(validate_report_is_deterministic(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_PRODUCTION_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
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
