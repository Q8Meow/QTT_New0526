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
    / "quantum_applicability_classification_registry.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "QuantumApplicabilityClassificationRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "quantum"
    / "synthetic_quantum_applicability_classification_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QuantumApplicabilityClassificationRegistry.report.json"
)

ALGORITHM_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "algorithms"
    / "QTTAlgorithmFormulaFamilyRegistry.yaml"
)
PARAMETER_LIFECYCLE_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomic_rows"
    / "AtomicRowsParameterLifecycleRegistry.yaml"
)
PARAMETER_AGENT_BINDING_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomic_rows"
    / "AtomicRowsParameterAgentBindingRegistry.yaml"
)
CURRENT_QUANTUM_SCHEMA_SURFACE = (
    pathlib.Path("schemas")
    / "dashboard_research_edge_quantum_risk"
    / "dashboard_research_edge_quantum_risk.schema.json"
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

REGISTRY_ID = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY"
REPORT_ID = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_REPORT"
REGISTRY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
REGISTRY_SCOPE = "STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY"
SUCCESS_MARKER = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
FAILURE_MARKER = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_FAILED"

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
PRIMARY_CLASS_ORDER = (
    "TRUE_QUANTUM",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUANTUM_INSPIRED",
    "CLASSICAL_ONLY",
)
PRIMARY_CLASSES = set(PRIMARY_CLASS_ORDER)
REASON_CODE_ORDER = (
    "QUANTUM_APPLICABILITY_ALLOWED_METADATA_ONLY",
    "QUANTUM_APPLICABILITY_ALLOWED_CLASSICAL_COMPARATOR",
    "QUANTUM_APPLICABILITY_ALLOWED_OWNER_OVERRIDE_INTERNAL_ONLY",
    "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID",
    "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_LABEL",
    "QUANTUM_APPLICABILITY_BLOCKED_DUPLICATE_FAMILY_ID",
    "QUANTUM_APPLICABILITY_BLOCKED_MISSING_REQUIRED_LABEL_COVERAGE",
    "QUANTUM_APPLICABILITY_BLOCKED_INVALID_PRIMARY_CLASS",
    "QUANTUM_APPLICABILITY_BLOCKED_CLASSICAL_ONLY_CONFLICT",
    "QUANTUM_APPLICABILITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_SCORING_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_RANKING_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_SELECTION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "QUANTUM_APPLICABILITY_BLOCKED_RANDOM_CLASSIFICATION_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "QUANTUM_APPLICABILITY_BLOCKED_CLASSIFICATION_REQUIRES_OWNER_REVIEW",
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
    "classification_is_metadata_only",
    "static_only_flag",
    "metadata_only_flag",
    "classical_only_families_valid_as_comparators",
    "future_owner_quantum_priority_policy_required",
    "future_scoring_policy_required",
    "future_optimizer_arbitration_required",
)
ROOT_FALSE_FIELDS = (
    "backend_execution_created",
    "random_classification_used",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "quantum_advantage_claim_created",
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
    "profit_evidence_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "owner_override_external_fact_fabrication_created",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "final_ready",
)
FAMILY_FALSE_FIELDS = (
    "owner_override_external_fact_fabrication_created",
    "external_fact_authority_created",
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "quantum_advantage_claim_created",
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
    "profit_evidence_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "capital_allocation_created",
    "live_portfolio_optimization_created",
)
FAMILY_TRUE_FIELDS = (
    "metadata_only_flag",
    "future_owner_quantum_priority_policy_required",
    "future_scoring_policy_required",
    "future_optimizer_arbitration_required",
)
BLOCKED_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "profit_evidence_created",
)
BLOCKED_TRUE_FIELDS = ("metadata_only_flag",)
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
}
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_REGISTRY_VALIDATES",
    "PASS_CLASSICAL_ONLY_COMPARATOR_VALID",
    "PASS_OWNER_OVERRIDE_INTERNAL_ONLY",
    "BLOCK_UNKNOWN_FAMILY_ID",
    "BLOCK_UNKNOWN_LABEL",
    "BLOCK_DUPLICATE_FAMILY_ID",
    "BLOCK_MISSING_REQUIRED_LABEL_COVERAGE",
    "BLOCK_INVALID_PRIMARY_CLASS",
    "BLOCK_CLASSICAL_ONLY_CONFLICT",
    "BLOCK_FORBIDDEN_EXECUTION_OR_AUTHORITY",
    "BLOCK_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "BLOCK_RANDOM_CLASSIFICATION",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
)


@dataclass(frozen=True)
class CanonicalFamily:
    family_id: str
    family_type: str
    source_registry: str


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


def _sort_labels(labels: Iterable[str]) -> list[str]:
    return _sort_by_order(labels, LABEL_ORDER)


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


def canonical_family_map(repo_root: pathlib.Path) -> dict[str, CanonicalFamily]:
    families: dict[str, CanonicalFamily] = {}

    algorithm_registry = load_yaml(_resolve(repo_root, ALGORITHM_REGISTRY))
    for family in _list_of_mappings(algorithm_registry.get("algorithm_families")):
        family_id = str(family.get("algorithm_family_id") or "")
        if family_id:
            families[family_id] = CanonicalFamily(
                family_id=family_id,
                family_type="ALGORITHM_FORMULA_FAMILY",
                source_registry=ALGORITHM_REGISTRY.as_posix(),
            )

    lifecycle_registry = load_yaml(_resolve(repo_root, PARAMETER_LIFECYCLE_REGISTRY))
    for entry in _list_of_mappings(lifecycle_registry.get("entries")):
        family_id = str(entry.get("parameter_family") or "")
        if family_id:
            families[family_id] = CanonicalFamily(
                family_id=family_id,
                family_type="ATOMICROWS_PARAMETER_LIFECYCLE_FAMILY",
                source_registry=PARAMETER_LIFECYCLE_REGISTRY.as_posix(),
            )

    binding_registry = load_yaml(_resolve(repo_root, PARAMETER_AGENT_BINDING_REGISTRY))
    for binding in _list_of_mappings(binding_registry.get("bindings")):
        family_id = str(binding.get("parameter_family") or "")
        if family_id:
            families[family_id] = CanonicalFamily(
                family_id=family_id,
                family_type="ATOMICROWS_PARAMETER_AGENT_BINDING_FAMILY",
                source_registry=PARAMETER_AGENT_BINDING_REGISTRY.as_posix(),
            )

    return {family_id: families[family_id] for family_id in sorted(families)}


def _expected_primary(labels: Sequence[str]) -> str | None:
    for primary in PRIMARY_CLASS_ORDER:
        if primary in labels:
            return primary
    return None


def _family_label(entry: dict[str, Any], index: int) -> str:
    family_id = entry.get("family_id")
    return str(family_id) if isinstance(family_id, str) and family_id else f"family_classifications[{index}]"


def _blocked_label(entry: dict[str, Any], index: int) -> str:
    family_id = entry.get("family_id")
    return str(family_id) if isinstance(family_id, str) and family_id else f"blocked_classifications[{index}]"


def _expected_reason_codes(entry: dict[str, Any]) -> list[str]:
    labels = entry.get("applicability_labels")
    label_values = labels if isinstance(labels, list) else []
    codes = (
        ["QUANTUM_APPLICABILITY_ALLOWED_CLASSICAL_COMPARATOR"]
        if label_values == ["CLASSICAL_ONLY"]
        else ["QUANTUM_APPLICABILITY_ALLOWED_METADATA_ONLY"]
    )
    if entry.get("owner_override_applied") is True:
        codes.append("QUANTUM_APPLICABILITY_ALLOWED_OWNER_OVERRIDE_INTERNAL_ONLY")
    return _sort_reason_codes(codes)


def validate_registry_payload(
    payload: dict[str, Any],
    canonical_families: dict[str, CanonicalFamily],
    *,
    label: str,
    require_canonical_coverage: bool = True,
) -> list[str]:
    failures: list[str] = []

    if payload.get("registry_id") != REGISTRY_ID:
        failures.append(f"{label}.registry_id must be {REGISTRY_ID}")
    if payload.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"{label}.semantic_task_id must be {SEMANTIC_TASK_ID}")
    if payload.get("registry_scope") != REGISTRY_SCOPE:
        failures.append(f"{label}.registry_scope must be {REGISTRY_SCOPE}")
    if payload.get("registry_version") != REGISTRY_VERSION:
        failures.append(f"{label}.registry_version must be {REGISTRY_VERSION}")

    for field in ROOT_TRUE_FIELDS:
        if payload.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in ROOT_FALSE_FIELDS:
        if payload.get(field) is not False:
            code = _reason_code_for_false_field(field)
            failures.append(f"{code}: {label}.{field} must be false")

    labels = payload.get("classification_labels")
    if labels != list(LABEL_ORDER):
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_MISSING_REQUIRED_LABEL_COVERAGE: "
            f"{label}.classification_labels must match canonical order"
        )
    reason_codes = payload.get("reason_codes")
    if reason_codes != list(REASON_CODE_ORDER):
        failures.append(f"{label}.reason_codes must match canonical deterministic order")

    classifications = _list_of_mappings(payload.get("family_classifications"))
    blocked = _list_of_mappings(payload.get("blocked_classifications"))
    classification_ids = [str(entry.get("family_id") or "") for entry in classifications]
    blocked_ids = [str(entry.get("family_id") or "") for entry in blocked]

    if classification_ids != sorted(classification_ids):
        failures.append(f"{label}.family_classifications must be sorted by family_id")
    if blocked_ids != sorted(blocked_ids):
        failures.append(f"{label}.blocked_classifications must be sorted by family_id")

    seen: set[str] = set()
    for family_id in classification_ids + blocked_ids:
        if family_id in seen:
            failures.append(
                "QUANTUM_APPLICABILITY_BLOCKED_DUPLICATE_FAMILY_ID: "
                f"{label} repeats family_id {family_id}"
            )
        seen.add(family_id)

    covered_family_ids = set(classification_ids) | set(blocked_ids)
    canonical_family_ids = set(canonical_families)
    unknown_ids = sorted(covered_family_ids - canonical_family_ids)
    if unknown_ids:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID: "
            f"{label} references unknown family IDs {', '.join(unknown_ids)}"
        )
    if require_canonical_coverage:
        missing = sorted(canonical_family_ids - covered_family_ids)
        if missing:
            failures.append(
                "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID: "
                f"{label} is missing canonical family IDs {', '.join(missing)}"
            )

    covered_labels: set[str] = set()
    for index, entry in enumerate(classifications):
        failures.extend(
            _validate_family_classification(
                entry,
                index=index,
                label=label,
                canonical_families=canonical_families,
            )
        )
        entry_labels = entry.get("applicability_labels")
        if isinstance(entry_labels, list):
            covered_labels.update(str(item) for item in entry_labels)

    missing_labels = [item for item in LABEL_ORDER if item not in covered_labels]
    if missing_labels:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_MISSING_REQUIRED_LABEL_COVERAGE: "
            f"{label} lacks label coverage for {', '.join(missing_labels)}"
        )

    for index, entry in enumerate(blocked):
        failures.extend(
            _validate_blocked_classification(
                entry,
                index=index,
                label=label,
                canonical_families=canonical_families,
            )
        )

    return failures


def _validate_family_classification(
    entry: dict[str, Any],
    *,
    index: int,
    label: str,
    canonical_families: dict[str, CanonicalFamily],
) -> list[str]:
    failures: list[str] = []
    family_id = str(entry.get("family_id") or "")
    entry_label = f"{label}.{_family_label(entry, index)}"
    canonical = canonical_families.get(family_id)

    if canonical is not None:
        if entry.get("family_type") != canonical.family_type:
            failures.append(f"{entry_label}.family_type must be {canonical.family_type}")
        if entry.get("family_registry_source") != canonical.source_registry:
            failures.append(f"{entry_label}.family_registry_source must be {canonical.source_registry}")
        if entry.get("source_registry") != canonical.source_registry:
            failures.append(f"{entry_label}.source_registry must be {canonical.source_registry}")
    elif entry.get("fixture_only") is not True:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID: "
            f"{entry_label}.family_id is not canonical"
        )

    for field in FAMILY_TRUE_FIELDS:
        if entry.get(field) is not True:
            failures.append(f"{entry_label}.{field} must be true")
    for field in FAMILY_FALSE_FIELDS:
        if entry.get(field) is not False:
            failures.append(f"{_reason_code_for_false_field(field)}: {entry_label}.{field} must be false")

    labels = entry.get("applicability_labels")
    label_values = labels if isinstance(labels, list) else []
    if not isinstance(labels, list) or not labels:
        failures.append(f"QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_LABEL: {entry_label}.applicability_labels must be a non-empty list")
        label_values = []
    unknown_labels = [str(item) for item in label_values if str(item) not in LABEL_ORDER]
    if unknown_labels:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_LABEL: "
            f"{entry_label}.applicability_labels has unknown labels {', '.join(unknown_labels)}"
        )
    if [str(item) for item in label_values] != _sort_labels(str(item) for item in label_values):
        failures.append(f"{entry_label}.applicability_labels must use canonical deterministic order")

    if "CLASSICAL_ONLY" in label_values and len(label_values) > 1:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_CLASSICAL_ONLY_CONFLICT: "
            f"{entry_label}.applicability_labels cannot combine CLASSICAL_ONLY with quantum labels"
        )

    primary = entry.get("primary_quantum_applicability_class")
    expected_primary = _expected_primary([str(item) for item in label_values])
    if primary not in PRIMARY_CLASSES:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_INVALID_PRIMARY_CLASS: "
            f"{entry_label}.primary_quantum_applicability_class is invalid"
        )
    elif expected_primary is None or primary != expected_primary:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_INVALID_PRIMARY_CLASS: "
            f"{entry_label}.primary_quantum_applicability_class must be {expected_primary}"
        )

    is_classical_only = label_values == ["CLASSICAL_ONLY"]
    if is_classical_only:
        if entry.get("classical_only_comparator_valid") is not True:
            failures.append(f"{entry_label}.classical_only_comparator_valid must be true")
        if entry.get("classical_comparator_required") is not False:
            failures.append(f"{entry_label}.classical_comparator_required must be false for CLASSICAL_ONLY")
    else:
        if entry.get("classical_only_comparator_valid") is not False:
            failures.append(f"{entry_label}.classical_only_comparator_valid must be false for quantum labels")
        if entry.get("classical_comparator_required") is not True:
            failures.append(f"{entry_label}.classical_comparator_required must be true for non-classical labels")

    basis = entry.get("owner_override_basis")
    if basis not in OWNER_OVERRIDE_BASES:
        failures.append(f"{entry_label}.owner_override_basis is not allowed")
    if entry.get("owner_override_applied") is True:
        if basis not in OWNER_OVERRIDE_ACTIVE_BASES:
            failures.append(f"{entry_label}.owner_override_basis must be active when owner_override_applied is true")
        if entry.get("owner_override_external_fact_fabrication_created") is not False:
            failures.append(
                "QUANTUM_APPLICABILITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT: "
                f"{entry_label}.owner_override_external_fact_fabrication_created must be false"
            )
    else:
        if basis != "NONE":
            failures.append(f"{entry_label}.owner_override_basis must be NONE when owner override is inactive")

    reason_codes = entry.get("reason_codes")
    if not isinstance(reason_codes, list):
        failures.append(f"{entry_label}.reason_codes must be a list")
    else:
        unknown_codes = [str(code) for code in reason_codes if str(code) not in REASON_CODE_ORDER]
        if unknown_codes:
            failures.append(f"{entry_label}.reason_codes has unknown codes {', '.join(unknown_codes)}")
        if [str(code) for code in reason_codes] != _sort_reason_codes(str(code) for code in reason_codes):
            failures.append(f"{entry_label}.reason_codes must use canonical deterministic order")
        expected_codes = _expected_reason_codes(entry)
        if [str(code) for code in reason_codes] != expected_codes:
            failures.append(f"{entry_label}.reason_codes must be {expected_codes}")

    blocked_reason_codes = entry.get("blocked_reason_codes")
    if blocked_reason_codes != []:
        failures.append(f"{entry_label}.blocked_reason_codes must be empty for valid classifications")

    return failures


def _validate_blocked_classification(
    entry: dict[str, Any],
    *,
    index: int,
    label: str,
    canonical_families: dict[str, CanonicalFamily],
) -> list[str]:
    failures: list[str] = []
    family_id = str(entry.get("family_id") or "")
    entry_label = f"{label}.{_blocked_label(entry, index)}"
    canonical = canonical_families.get(family_id)

    if canonical is not None:
        if entry.get("family_type") != canonical.family_type:
            failures.append(f"{entry_label}.family_type must be {canonical.family_type}")
        if entry.get("family_registry_source") != canonical.source_registry:
            failures.append(f"{entry_label}.family_registry_source must be {canonical.source_registry}")
        if entry.get("source_registry") != canonical.source_registry:
            failures.append(f"{entry_label}.source_registry must be {canonical.source_registry}")
    elif entry.get("fixture_only") is not True:
        failures.append(
            "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID: "
            f"{entry_label}.family_id is not canonical"
        )

    for field in BLOCKED_TRUE_FIELDS:
        if entry.get(field) is not True:
            failures.append(f"{entry_label}.{field} must be true")
    for field in BLOCKED_FALSE_FIELDS:
        if entry.get(field) is not False:
            failures.append(f"{_reason_code_for_false_field(field)}: {entry_label}.{field} must be false")

    codes = entry.get("blocked_reason_codes")
    if not isinstance(codes, list) or not codes:
        failures.append(f"{entry_label}.blocked_reason_codes must be a non-empty list")
    else:
        unknown_codes = [str(code) for code in codes if str(code) not in REASON_CODE_ORDER]
        if unknown_codes:
            failures.append(f"{entry_label}.blocked_reason_codes has unknown codes {', '.join(unknown_codes)}")
        if [str(code) for code in codes] != _sort_reason_codes(str(code) for code in codes):
            failures.append(f"{entry_label}.blocked_reason_codes must use canonical deterministic order")
    return failures


def _reason_code_for_false_field(field: str) -> str:
    field_map = {
        "backend_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_backend_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_simulator_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
        "qaoa_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
        "vqe_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_VQE_EXECUTION_FORBIDDEN",
        "annealing_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
        "qubo_solve_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_QUBO_SOLVE_FORBIDDEN",
        "ising_solve_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_ISING_SOLVE_FORBIDDEN",
        "optimizer_arbitration_created": "QUANTUM_APPLICABILITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
        "scoring_execution_created": "QUANTUM_APPLICABILITY_BLOCKED_SCORING_FORBIDDEN",
        "ranking_created": "QUANTUM_APPLICABILITY_BLOCKED_RANKING_FORBIDDEN",
        "selection_created": "QUANTUM_APPLICABILITY_BLOCKED_SELECTION_FORBIDDEN",
        "runtime_authority_created": "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "live_authority_created": "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "order_authority_created": "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "source_retrieval_created": "QUANTUM_APPLICABILITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "source_acceptance_created": "QUANTUM_APPLICABILITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "connector_semantic_binding_created": "QUANTUM_APPLICABILITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
        "quantum_advantage_claim_created": "QUANTUM_APPLICABILITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        "profit_evidence_created": "QUANTUM_APPLICABILITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "latency_superiority_claim_created": "QUANTUM_APPLICABILITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
        "execution_superiority_claim_created": "QUANTUM_APPLICABILITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
        "owner_override_external_fact_fabrication_created": "QUANTUM_APPLICABILITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
        "random_classification_used": "QUANTUM_APPLICABILITY_BLOCKED_RANDOM_CLASSIFICATION_FORBIDDEN",
        "atomicrows_bundle_jsonl_created": "QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
        "atomicrows_bundle_sha256_created": "QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
        "external_fact_authority_created": "QUANTUM_APPLICABILITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
        "capital_allocation_created": "QUANTUM_APPLICABILITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "live_portfolio_optimization_created": "QUANTUM_APPLICABILITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    }
    return field_map.get(field, "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_LABEL")


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependencies = _list_of_mappings(payload.get("depends_on_artifacts"))
    ids = [str(item.get("artifact_id") or "") for item in dependencies]
    if ids != sorted(DEPENDENCY_MARKERS):
        failures.append("depends_on_artifacts must list PR65-PR68 and PR73-PR81 artifact IDs in deterministic order")
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


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    for field in (
        "external_fact_authority_created",
        "runtime_authority_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "optimizer_arbitration_created",
        "scoring_execution_created",
        "ranking_created",
        "selection_created",
        "profit_evidence_created",
        "random_classification_used",
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
            "QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    if not (_resolve(repo_root, PR76_SHORT_TEST)).exists():
        failures.append(f"PR76 short runtime resolver allowlist test is missing: {PR76_SHORT_TEST.as_posix()}")
    if (_resolve(repo_root, PR76_OLD_LONG_TEST)).exists():
        failures.append(f"old long runtime resolver allowlist filename must remain absent: {PR76_OLD_LONG_TEST.as_posix()}")
    if not (_resolve(repo_root, CURRENT_QUANTUM_SCHEMA_SURFACE)).exists():
        failures.append(f"current quantum schema surface missing: {CURRENT_QUANTUM_SCHEMA_SURFACE.as_posix()}")
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
        return [f"{MASTER_PLAN_CURRENT.as_posix()} has local diff; PR82 must not edit it"]
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
    canonical_families: dict[str, CanonicalFamily],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    classifications = _list_of_mappings(payload.get("family_classifications"))
    blocked = _list_of_mappings(payload.get("blocked_classifications"))
    classified_ids = sorted(str(entry.get("family_id") or "") for entry in classifications)
    blocked_ids = sorted(str(entry.get("family_id") or "") for entry in blocked)
    labels_present = _sort_labels(
        str(label)
        for entry in classifications
        for label in (entry.get("applicability_labels") if isinstance(entry.get("applicability_labels"), list) else [])
    )
    primary_counts = {
        primary: sum(1 for entry in classifications if entry.get("primary_quantum_applicability_class") == primary)
        for primary in PRIMARY_CLASS_ORDER
    }
    return {
        "report_id": REPORT_ID,
        "report_version": REGISTRY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "registry_id": payload.get("registry_id"),
        "semantic_task_id": payload.get("semantic_task_id"),
        "registry_scope": payload.get("registry_scope"),
        "classification_is_metadata_only": True,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "classification_labels": list(LABEL_ORDER),
        "classification_labels_present": labels_present,
        "classification_label_count": len(LABEL_ORDER),
        "canonical_family_count": len(canonical_families),
        "family_classification_count": len(classifications),
        "blocked_classification_count": len(blocked),
        "classified_family_ids": classified_ids,
        "blocked_family_ids": blocked_ids,
        "missing_canonical_family_ids": sorted(set(canonical_families) - set(classified_ids) - set(blocked_ids)),
        "primary_quantum_applicability_class_counts": primary_counts,
        "classical_only_families_valid_as_comparators": True,
        "future_owner_quantum_priority_policy_required": True,
        "future_scoring_policy_required": True,
        "future_optimizer_arbitration_required": True,
        "backend_execution_created": False,
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_solve_execution_created": False,
        "ising_solve_execution_created": False,
        "quantum_advantage_claim_created": False,
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
        "profit_evidence_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "owner_override_external_fact_fabrication_created": False,
        "random_classification_used": False,
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

    try:
        canonical_families = canonical_family_map(repo_root)
    except (OSError, ValueError, RegistryParseError, json.JSONDecodeError) as exc:
        return ValidationResult(False, tuple(failures + [f"CANONICAL_FAMILY_LOAD_FAILED: {exc}"]), None)

    failures.extend(validate_dependencies(registry, repo_root))
    failures.extend(validate_registry_payload(registry, canonical_families, label="REGISTRY"))
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(registry, canonical_families, repo_root)
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
