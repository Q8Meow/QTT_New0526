#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import (  # noqa: E402
    validate_atomicrows_research_provenance_evidence_tier_classification as pr70_gate,
)
from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_owner_submitted_research_source_intake_registry.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_owner_submitted_research_source_intake_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
)
DEFAULT_PR70_SCHEMA = pr70_gate.DEFAULT_SCHEMA
DEFAULT_PR70_REGISTRY = pr70_gate.DEFAULT_REGISTRY
DEFAULT_PR70_REPORT = pr70_gate.DEFAULT_REPORT

CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
FORBIDDEN_ARTIFACT_PATHS = (CANONICAL_BUNDLE_JSONL, CANONICAL_BUNDLE_SHA256)

REGISTRY_ID = "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY"
REGISTRY_VERSION = "v1"
REPORT_ID = "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
AUTHORITY_CLASS = (
    "STATIC_OWNER_RESEARCH_INTAKE_REGISTRY_NOT_SOURCE_FACT_NOT_ACCEPTED_PACKET_"
    "NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = "STATIC_VALIDATION_REPORT_NOT_SOURCE_FACT_NOT_RUNTIME_AUTHORITY"
SUCCESS_MARKER = "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_OK"
FAILURE_MARKER = "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_FINAL_INCOMPLETE"
)

CANONICAL_SOURCE_TYPES = tuple(pr70_gate.CANONICAL_SOURCE_TYPES)

ROADMAP_REQUIRED_ENTRY_FIELDS = (
    "source_intake_id",
    "source_type",
    "source_locator",
    "owner_note",
    "target_parameter_family",
    "target_algorithm_family",
    "target_agent_role",
    "research_hypothesis",
    "owner_approved",
    "owner_override_satisfaction_basis",
    "candidate_route",
)
QUANTUM_FORWARD_ENTRY_FIELDS = (
    "quantum_relevance_requested",
    "quantum_route_requested",
    "quantum_applicability_review_requested",
    "target_quantum_algorithm_family",
    "owner_quantum_priority_requested",
)
ENTRY_REQUIRED_FIELDS = ROADMAP_REQUIRED_ENTRY_FIELDS + QUANTUM_FORWARD_ENTRY_FIELDS

CANDIDATE_ROUTES_SUPPORTED = (
    "RESEARCH_ARCHIVE_ONLY",
    "PR72_PARAMETER_FAMILY_CANDIDATE_REVIEW",
    "PR72_ALGORITHM_FAMILY_CANDIDATE_REVIEW",
    "PR72_AGENT_BINDING_REQUEST_REVIEW",
    "PR72_OWNER_OVERRIDE_RECEIPT_REFERENCE_REVIEW",
    "RETRIEVAL_TARGET_REVIEW_ONLY",
    "OWNER_REVIEW_REQUIRED",
    "BLOCKED_NO_OWNER_APPROVAL",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
)
QUANTUM_ROUTES_SUPPORTED = (
    "NONE",
    "QUANTUM_RESEARCH_REVIEW",
    "QUANTUM_OPTIMIZER_CANDIDATE_REVIEW",
    "TRUE_QUANTUM_REVIEW",
    "QUANTUM_INSPIRED_REVIEW",
    "HYBRID_CLASSICAL_QUANTUM_REVIEW",
    "QUBO_COMPATIBILITY_REVIEW",
    "ISING_COMPATIBILITY_REVIEW",
    "QAOA_COMPATIBILITY_REVIEW",
    "VQE_COMPATIBILITY_REVIEW",
    "ANNEALING_COMPATIBILITY_REVIEW",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_REVIEW",
    "OWNER_FORCED_QUANTUM_REVIEW",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
)
TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED = (
    "OWNER_UNSET_PENDING_REVIEW",
    "NONE",
    "TRUE_QUANTUM_OPTIMIZER",
    "QUANTUM_INSPIRED_OPTIMIZER",
    "HYBRID_CLASSICAL_QUANTUM_OPTIMIZER",
    "QUBO_COMPATIBLE_ALGORITHM",
    "ISING_COMPATIBLE_ALGORITHM",
    "QAOA_COMPATIBLE_ALGORITHM",
    "VQE_COMPATIBLE_ALGORITHM",
    "ANNEALING_COMPATIBLE_ALGORITHM",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_FAMILY",
)
OWNER_OVERRIDE_SATISFACTION_BASES = (
    "OWNER_UNSET",
    "OWNER_APPROVED",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_OVERRIDE_SATISFIED",
    "SYNTHETIC_NOT_REAL_OWNER_APPROVAL",
)

DEPENDENCY_FIELDS = ("schema_path", "registry_path", "report_path")
FORBIDDEN_ARTIFACT_FLAG_FIELDS = (
    "source_retrieval",
    "source_acceptance",
    "accepted_source_packets",
    "connector_semantics",
    "runtime_artifacts",
    "runtime_receipts",
    "live_receipts",
    "order_receipts",
    "cash_receipts",
    "replay_results",
    "paper_results",
    "live_readiness",
    "order_authority",
    "profit_evidence",
    "quantum_backend_evidence",
    "quantum_advantage_claim",
    "latency_superiority_claim",
    "execution_superiority_claim",
    "atomicrows_bundle_rows",
    "pr72_conversion",
)
TOP_LEVEL_FALSE_FIELDS = (
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_packets",
    "creates_connector_semantics",
    "creates_runtime_artifacts",
    "creates_atomicrows_bundle_rows",
    "creates_replay_results",
    "creates_paper_results",
    "creates_live_readiness",
    "creates_order_authority",
    "creates_profit_evidence",
    "creates_quantum_backend_evidence",
    "creates_quantum_advantage_claim",
    "creates_latency_superiority_claim",
    "creates_execution_superiority_claim",
    "implements_pr72_conversion",
    "candidate_parameter_family_packet_created",
    "candidate_algorithm_family_packet_created",
    "candidate_agent_binding_request_created",
    "owner_override_receipt_reference_created",
)
OWNER_OVERRIDE_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfaction_basis_supported",
    "owner_override_satisfies_internal_workflow_only",
)
OWNER_OVERRIDE_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
)
NO_SELECTION_FALSE_FIELDS = (
    "implements_random_selection",
    "implements_ranking",
    "implements_scoring",
    "implements_arbitration",
    "implements_trade_context_routing",
    "implements_stack_selection",
    "implements_quantum_classical_arbitration",
)
TOP_LEVEL_REQUIRED_FIELDS = (
    "registry_id",
    "registry_version",
    "authority_class",
    "depends_on_provenance_classifier",
    "source_type_count_expected",
    "supported_source_types",
    "roadmap_required_entry_fields",
    "quantum_forward_entry_fields",
    "candidate_routes_supported",
    "quantum_routes_supported",
    "target_quantum_algorithm_families_supported",
    "real_owner_intake_entry_count",
    "real_owner_intakes_invented",
    "synthetic_fixture_only",
    "intake_entries",
    "forbidden_artifact_flags",
    *TOP_LEVEL_FALSE_FIELDS,
    *OWNER_OVERRIDE_TRUE_FIELDS,
    *OWNER_OVERRIDE_FALSE_FIELDS,
    *NO_SELECTION_FALSE_FIELDS,
    "final_ready",
)
REPORT_FALSE_FIELDS = (
    "real_urls_present",
    "real_source_claims_present",
    "secrets_present",
    "external_repo_commands_present",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "runtime_artifacts_created",
    "runtime_receipts_created",
    "live_receipts_created",
    "order_receipts_created",
    "cash_receipts_created",
    "replay_results_created",
    "paper_results_created",
    "live_readiness_created",
    "order_authority_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "atomicrows_bundle_jsonl_exists",
    "atomicrows_bundle_sha256_exists",
    "pr72_conversion_implemented",
    "candidate_parameter_family_packet_created",
    "candidate_algorithm_family_packet_created",
    "candidate_agent_binding_request_created",
    "owner_override_receipt_reference_created",
)

SYNTHETIC_LOCATOR = "SYNTHETIC_LOCATOR_NO_EXTERNAL_FETCH"
SYNTHETIC_ENTRY_ID_PREFIX = "SYNTHETIC-OSRSIR-"
ENTRY_ID_PATTERN = re.compile(r"^(OSRSIR|SYNTHETIC-OSRSIR)-[A-Z0-9_-]+$")


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"fixture root must be an object: {path}")
    return value


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _load_json_checked(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"DEPENDENCY_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"DEPENDENCY_MALFORMED: JSON file is invalid: {path}: {exc}"]


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
        ("ACCOUNT_BALANCE_CLAIM", "account" + " balance"),
        ("OPEN_ORDERS_CLAIM", "open" + " orders"),
        ("RUNTIME_CASH_CLAIM", "runtime" + " cash"),
        ("EXTERNAL_REPO_CLONE_COMMAND", "git" + " clone"),
        ("PACKAGE_INSTALL_COMMAND_PIP", "pip" + " install"),
        ("PACKAGE_INSTALL_COMMAND_NPM", "npm" + " install"),
        ("PACKAGE_INSTALL_COMMAND_UV", "uv" + " pip"),
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
    )


def _forbidden_text_regexes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    return (
        ("SECRET_LIKE_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("ORDER_FILL_CLAIM", re.compile(r"\bfills\b", re.IGNORECASE)),
    )


def forbidden_text_findings(texts: Sequence[tuple[str, str]]) -> dict[str, bool]:
    findings = {
        "real_urls_present": False,
        "real_source_claims_present": False,
        "secrets_present": False,
        "external_repo_commands_present": False,
        "forbidden_claims_present": False,
    }
    secret_codes = {
        "SECRET_LIKE_API_KEY",
        "SECRET_LIKE_API_KEY_UNDERSCORE",
        "SECRET_LIKE_PRIVATE_KEY",
        "SECRET_LIKE_BEARER_TOKEN",
        "SECRET_LIKE_PASSWORD",
        "SECRET_LIKE_AWS_ACCESS_KEY",
    }
    source_claim_codes = {
        "SOURCE_ACCEPTANCE_CLAIM",
        "CONNECTOR_SEMANTIC_CLAIM",
    }
    external_command_codes = {
        "EXTERNAL_REPO_CLONE_COMMAND",
        "PACKAGE_INSTALL_COMMAND_PIP",
        "PACKAGE_INSTALL_COMMAND_NPM",
        "PACKAGE_INSTALL_COMMAND_UV",
    }
    url_codes = {"REAL_HTTP_LOCATOR", "REAL_HTTPS_LOCATOR", "REAL_WWW_LOCATOR"}
    for _, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() not in lowered:
                continue
            findings["forbidden_claims_present"] = True
            if code in url_codes:
                findings["real_urls_present"] = True
            if code in secret_codes:
                findings["secrets_present"] = True
            if code in source_claim_codes:
                findings["real_source_claims_present"] = True
            if code in external_command_codes:
                findings["external_repo_commands_present"] = True
        for code, pattern in _forbidden_text_regexes():
            if not pattern.search(text):
                continue
            findings["forbidden_claims_present"] = True
            if code in secret_codes:
                findings["secrets_present"] = True
            if code == "ORDER_FILL_CLAIM":
                findings["real_source_claims_present"] = True
    return findings


def validate_no_forbidden_artifact_text(
    texts: Sequence[tuple[str, str]],
) -> list[str]:
    failures: list[str] = []
    for label, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() in lowered:
                failures.append(f"{code}: forbidden text appears in {label}")
        for code, pattern in _forbidden_text_regexes():
            if pattern.search(text):
                failures.append(f"{code}: forbidden text appears in {label}")
    return failures


def validate_no_forbidden_artifacts(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    root = repo_root.resolve()
    for rel_path in FORBIDDEN_ARTIFACT_PATHS:
        if (root / rel_path).exists():
            failures.append(f"FORBIDDEN_ARTIFACT_EXISTS: {_as_posix(rel_path)}")
    return failures


def _expected_dependency() -> dict[str, str]:
    return {
        "schema_path": _as_posix(DEFAULT_PR70_SCHEMA),
        "registry_path": _as_posix(DEFAULT_PR70_REGISTRY),
        "report_path": _as_posix(DEFAULT_PR70_REPORT),
    }


def _pr70_source_types_from_registry(registry: dict[str, Any]) -> list[str]:
    ids = registry.get("source_type_ids_canonical_order")
    if isinstance(ids, list):
        return [str(item) for item in ids]
    entries = registry.get("source_types")
    if isinstance(entries, list):
        return [
            str(entry.get("source_type"))
            for entry in entries
            if isinstance(entry, dict) and entry.get("source_type") is not None
        ]
    return []


def validate_pr70_dependency(
    *,
    repo_root: pathlib.Path,
    pr70_schema_path: pathlib.Path,
    pr70_registry_path: pathlib.Path,
    pr70_report_path: pathlib.Path,
) -> tuple[list[str], list[str]]:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json_checked(root / pr70_schema_path)
    report, report_failures = _load_json_checked(root / pr70_report_path)
    failures.extend(schema_failures)
    failures.extend(report_failures)
    try:
        registry = load_registry(root / pr70_registry_path)
    except (OSError, RegistryParseError) as exc:
        failures.append(
            f"PR70_CLASSIFIER_DEPENDENCY_MALFORMED: registry is invalid: {exc}"
        )
        registry = {}

    registry_source_types = _pr70_source_types_from_registry(registry)
    report_source_types = []
    if isinstance(report, dict):
        report_source_types = [
            str(item) for item in report.get("source_type_ids", []) if item is not None
        ]
    schema_source_types = []
    if isinstance(schema, dict):
        source_type_def = _mapping(
            _mapping(schema.get("$defs")).get("source_type_id")
        )
        schema_source_types = [
            str(item) for item in source_type_def.get("enum", [])
        ]

    expected = list(CANONICAL_SOURCE_TYPES)
    observed_candidates = (
        ("registry", registry_source_types),
        ("report", report_source_types),
        ("schema", schema_source_types),
    )
    for label, source_types in observed_candidates:
        if source_types != expected:
            failures.append(
                f"PR70_SOURCE_TYPE_UNIVERSE_MISMATCH: {label} source types must "
                f"match canonical PR70 source types"
            )

    if isinstance(registry, dict):
        if registry.get("source_type_count") != len(expected):
            failures.append("PR70_SOURCE_TYPE_COUNT_MISMATCH: registry count must be 14")
    if isinstance(report, dict):
        expected_report_values = {
            "source_type_count": len(expected),
            "required_source_type_count": len(expected),
            "required_source_types_present_count": len(expected),
            "forbidden_source_type_boundary_true_count": 0,
            "final_ready": False,
            "source_retrieval_executed": False,
            "source_acceptance_executed": False,
            "accepted_source_packet_created": False,
            "connector_binding_created": False,
            "runtime_artifact_created": False,
            "live_artifact_created": False,
            "order_artifact_created": False,
            "profit_evidence_created": False,
            "alpha_evidence_created": False,
            "latency_superiority_evidence_created": False,
            "execution_superiority_evidence_created": False,
            "quantum_advantage_evidence_created": False,
            "quantum_backend_artifact_created": False,
            "bundle_file_present": False,
            "bundle_sha_present": False,
            "uses_pr_number_as_authority": False,
        }
        for field, expected_value in expected_report_values.items():
            if report.get(field) != expected_value:
                failures.append(
                    f"PR70_REPORT_FIELD_MISMATCH: {field} must be {expected_value!r}"
                )
    return expected, failures


def _require_exact_keys(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    expected = set(expected_fields)
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"{label}: missing required fields {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label}: unexpected fields {', '.join(unexpected)}")
    return failures


def validate_schema_surface(
    schema: dict[str, Any],
    *,
    pr70_source_types: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_LEVEL_REQUIRED_FIELDS):
        failures.append("schema.required must match PR71 registry required fields")

    defs = _mapping(schema.get("$defs"))
    source_type_id = _mapping(defs.get("source_type_id"))
    if source_type_id.get("enum") != list(pr70_source_types):
        failures.append("schema.$defs.source_type_id enum must match PR70")
    candidate_route = _mapping(defs.get("candidate_route"))
    if candidate_route.get("enum") != list(CANDIDATE_ROUTES_SUPPORTED):
        failures.append("schema.$defs.candidate_route enum must be canonical")
    quantum_route = _mapping(defs.get("quantum_route"))
    if quantum_route.get("enum") != list(QUANTUM_ROUTES_SUPPORTED):
        failures.append("schema.$defs.quantum_route enum must be canonical")
    target_family = _mapping(defs.get("target_quantum_algorithm_family"))
    if target_family.get("enum") != list(
        TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED
    ):
        failures.append(
            "schema.$defs.target_quantum_algorithm_family enum must be canonical"
        )

    dependency = _mapping(defs.get("provenance_classifier_dependency"))
    if dependency.get("required") != list(DEPENDENCY_FIELDS):
        failures.append("schema classifier dependency required fields must be exact")
    if dependency.get("additionalProperties") is not False:
        failures.append("schema classifier dependency additionalProperties must be false")

    flags = _mapping(defs.get("forbidden_artifact_flags"))
    if flags.get("required") != list(FORBIDDEN_ARTIFACT_FLAG_FIELDS):
        failures.append("schema forbidden artifact flag fields must be exact")
    if flags.get("additionalProperties") is not False:
        failures.append("schema forbidden artifact flags additionalProperties must be false")

    intake_entry = _mapping(defs.get("intake_entry"))
    if intake_entry.get("additionalProperties") is not False:
        failures.append("schema intake_entry additionalProperties must be false")
    if intake_entry.get("required") != list(ENTRY_REQUIRED_FIELDS):
        failures.append("schema intake_entry required fields must be exact")
    intake_properties = _mapping(intake_entry.get("properties"))
    for field in ENTRY_REQUIRED_FIELDS:
        if field not in intake_properties:
            failures.append(f"schema intake_entry missing property {field}")
    supported_const = _mapping(_mapping(schema.get("properties")).get("supported_source_types")).get(
        "const"
    )
    if supported_const != list(pr70_source_types):
        failures.append("schema supported_source_types const must match PR70")
    return failures


def _validate_entry(
    entry: dict[str, Any],
    *,
    label: str,
    pr70_source_types: Sequence[str],
    synthetic_only: bool,
) -> list[str]:
    failures: list[str] = []
    failures.extend(_require_exact_keys(entry, ENTRY_REQUIRED_FIELDS, label))
    source_intake_id = entry.get("source_intake_id")
    if not isinstance(source_intake_id, str) or not ENTRY_ID_PATTERN.match(
        source_intake_id
    ):
        failures.append(f"{label}.source_intake_id must match deterministic pattern")
    is_synthetic = (
        isinstance(source_intake_id, str)
        and source_intake_id.startswith(SYNTHETIC_ENTRY_ID_PREFIX)
    )
    if synthetic_only and not is_synthetic:
        failures.append(f"{label}.source_intake_id must be synthetic-only")
    if entry.get("source_type") not in pr70_source_types:
        failures.append(f"{label}.source_type is not supported by PR70")
    if entry.get("candidate_route") not in CANDIDATE_ROUTES_SUPPORTED:
        failures.append(f"{label}.candidate_route is not supported")
    if entry.get("quantum_route_requested") not in QUANTUM_ROUTES_SUPPORTED:
        failures.append(f"{label}.quantum_route_requested is not supported")
    if (
        entry.get("target_quantum_algorithm_family")
        not in TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED
    ):
        failures.append(f"{label}.target_quantum_algorithm_family is not supported")
    if entry.get("owner_override_satisfaction_basis") not in OWNER_OVERRIDE_SATISFACTION_BASES:
        failures.append(f"{label}.owner_override_satisfaction_basis is not supported")

    if is_synthetic:
        if entry.get("source_locator") != SYNTHETIC_LOCATOR:
            failures.append(f"{label}.source_locator must be non-fetchable synthetic")
        if entry.get("owner_approved") is not False:
            failures.append(f"{label}.owner_approved must be false for synthetic rows")
        if (
            entry.get("owner_override_satisfaction_basis")
            != "SYNTHETIC_NOT_REAL_OWNER_APPROVAL"
        ):
            failures.append(
                f"{label}.owner_override_satisfaction_basis must be synthetic-only"
            )
        if entry.get("candidate_route") != "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE":
            failures.append(f"{label}.candidate_route must be synthetic-only")
    return failures


def validate_registry_payload(
    payload: dict[str, Any],
    *,
    label: str,
    pr70_source_types: Sequence[str],
    production: bool,
    synthetic_only_entries: bool,
) -> list[str]:
    failures: list[str] = []
    failures.extend(_require_exact_keys(payload, TOP_LEVEL_REQUIRED_FIELDS, label))
    expected_values: dict[str, Any] = {
        "registry_id": REGISTRY_ID,
        "registry_version": REGISTRY_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "source_type_count_expected": len(pr70_source_types),
        "supported_source_types": list(pr70_source_types),
        "roadmap_required_entry_fields": list(ROADMAP_REQUIRED_ENTRY_FIELDS),
        "quantum_forward_entry_fields": list(QUANTUM_FORWARD_ENTRY_FIELDS),
        "candidate_routes_supported": list(CANDIDATE_ROUTES_SUPPORTED),
        "quantum_routes_supported": list(QUANTUM_ROUTES_SUPPORTED),
        "target_quantum_algorithm_families_supported": list(
            TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED
        ),
        "real_owner_intakes_invented": False,
        "synthetic_fixture_only": True,
        "final_ready": False,
        **{field: False for field in TOP_LEVEL_FALSE_FIELDS},
        **{field: True for field in OWNER_OVERRIDE_TRUE_FIELDS},
        **{field: False for field in OWNER_OVERRIDE_FALSE_FIELDS},
        **{field: False for field in NO_SELECTION_FALSE_FIELDS},
    }
    for field, expected in expected_values.items():
        if payload.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")

    dependency = payload.get("depends_on_provenance_classifier")
    if not isinstance(dependency, dict):
        failures.append(f"{label}.depends_on_provenance_classifier must be an object")
    elif dependency != _expected_dependency():
        failures.append(
            f"{label}.depends_on_provenance_classifier must match PR70 paths"
        )

    forbidden_flags = payload.get("forbidden_artifact_flags")
    if not isinstance(forbidden_flags, dict):
        failures.append(f"{label}.forbidden_artifact_flags must be an object")
    else:
        failures.extend(
            _require_exact_keys(
                forbidden_flags,
                FORBIDDEN_ARTIFACT_FLAG_FIELDS,
                f"{label}.forbidden_artifact_flags",
            )
        )
        for field in FORBIDDEN_ARTIFACT_FLAG_FIELDS:
            if forbidden_flags.get(field) is not False:
                failures.append(
                    f"{label}.forbidden_artifact_flags.{field} must be false"
                )

    entries = payload.get("intake_entries")
    if not isinstance(entries, list):
        failures.append(f"{label}.intake_entries must be a list")
        entries = []
    real_count = payload.get("real_owner_intake_entry_count")
    if not isinstance(real_count, int) or isinstance(real_count, bool):
        failures.append(f"{label}.real_owner_intake_entry_count must be an integer")
    elif real_count != 0:
        failures.append(f"{label}.real_owner_intake_entry_count must be 0")
    if production and entries != []:
        failures.append(f"{label}.intake_entries must be empty for PR71 production")

    seen_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        entry_label = f"{label}.intake_entries[{index}]"
        if not isinstance(entry, dict):
            failures.append(f"{entry_label} must be an object")
            continue
        source_intake_id = entry.get("source_intake_id")
        if isinstance(source_intake_id, str):
            if source_intake_id in seen_ids:
                failures.append(f"{entry_label}.source_intake_id is duplicated")
            seen_ids.add(source_intake_id)
        failures.extend(
            _validate_entry(
                entry,
                label=entry_label,
                pr70_source_types=pr70_source_types,
                synthetic_only=synthetic_only_entries,
            )
        )

    text = json.dumps(payload, sort_keys=True)
    failures.extend(validate_no_forbidden_artifact_text(((label, text),)))
    return failures


def _fixture_cases(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    cases = fixture.get("fixture_cases")
    if isinstance(cases, list):
        return [case for case in cases if isinstance(case, dict)]
    return []


def validate_fixture_payload(
    fixture: dict[str, Any],
    *,
    schema: dict[str, Any],
    pr70_source_types: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    expected_root_fields = (
        "fixture_id",
        "fixture_version",
        "mode",
        "execution",
        "fixture_cases",
    )
    failures.extend(_require_exact_keys(fixture, expected_root_fields, "fixture"))
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    cases = _fixture_cases(fixture)
    if len(cases) != 2:
        failures.append("fixture.fixture_cases must contain exactly two cases")
    case_ids = [case.get("case_id") for case in cases]
    if case_ids != [
        "SYNTHETIC_EMPTY_PRODUCTION_REGISTRY_CASE",
        "SYNTHETIC_INERT_INTAKE_ENTRY_CASE",
    ]:
        failures.append("fixture.fixture_cases must be in canonical case order")
    for index, case in enumerate(cases, start=1):
        label = f"fixture.fixture_cases[{index}]"
        failures.extend(_require_exact_keys(case, ("case_id", "registry"), label))
        registry = case.get("registry")
        if not isinstance(registry, dict):
            failures.append(f"{label}.registry must be an object")
            continue
        failures.extend(
            validate_json_schema_subset(registry, schema, root_schema=schema)
        )
        failures.extend(
            validate_registry_payload(
                registry,
                label=f"{label}.registry",
                pr70_source_types=pr70_source_types,
                production=False,
                synthetic_only_entries=True,
            )
        )
    if cases:
        first_registry = _mapping(cases[0].get("registry"))
        if first_registry.get("intake_entries") != []:
            failures.append("fixture empty production case must have no intake entries")
    if len(cases) > 1:
        second_registry = _mapping(cases[1].get("registry"))
        second_entries = second_registry.get("intake_entries")
        if not isinstance(second_entries, list) or len(second_entries) != 1:
            failures.append("fixture inert intake case must contain one synthetic entry")
    text = json.dumps(fixture, sort_keys=True)
    failures.extend(validate_no_forbidden_artifact_text((("fixture", text),)))
    return failures


def fixture_contains_only_synthetic_entries(fixture: dict[str, Any]) -> bool:
    for case in _fixture_cases(fixture):
        registry = _mapping(case.get("registry"))
        entries = registry.get("intake_entries")
        if not isinstance(entries, list):
            return False
        for entry in entries:
            if not isinstance(entry, dict):
                return False
            source_intake_id = entry.get("source_intake_id")
            if (
                not isinstance(source_intake_id, str)
                or not source_intake_id.startswith(SYNTHETIC_ENTRY_ID_PREFIX)
                or entry.get("source_locator") != SYNTHETIC_LOCATOR
                or entry.get("owner_approved") is not False
                or entry.get("candidate_route")
                != "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE"
                or entry.get("owner_override_satisfaction_basis")
                != "SYNTHETIC_NOT_REAL_OWNER_APPROVAL"
            ):
                return False
    return True


def _flag_from_registry(
    registry: dict[str, Any],
    field: str,
    *,
    default: bool = False,
) -> bool:
    return bool(registry.get(field, default))


def build_report(
    *,
    repo_root: pathlib.Path,
    registry: dict[str, Any],
    fixture: dict[str, Any],
    pr70_source_types: Sequence[str],
    artifact_findings: dict[str, bool],
    pr70_report_path: pathlib.Path,
    production_registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    root = repo_root.resolve()
    entries = registry.get("intake_entries", [])
    entry_count = len(entries) if isinstance(entries, list) else 0
    return {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "depends_on_pr70_classifier": True,
        "pr70_classifier_report_path": _as_posix(pr70_report_path),
        "pr70_source_type_count_observed": len(pr70_source_types),
        "supported_source_type_count": len(registry.get("supported_source_types", [])),
        "roadmap_required_entry_field_count": len(ROADMAP_REQUIRED_ENTRY_FIELDS),
        "quantum_forward_entry_field_count": len(QUANTUM_FORWARD_ENTRY_FIELDS),
        "required_entry_fields_present": registry.get(
            "roadmap_required_entry_fields"
        )
        == list(ROADMAP_REQUIRED_ENTRY_FIELDS),
        "quantum_forward_fields_present": registry.get(
            "quantum_forward_entry_fields"
        )
        == list(QUANTUM_FORWARD_ENTRY_FIELDS),
        "production_registry_path": _as_posix(production_registry_path),
        "production_intake_entries_count": entry_count,
        "real_owner_intake_entry_count": registry.get("real_owner_intake_entry_count"),
        "real_owner_intakes_invented": registry.get("real_owner_intakes_invented"),
        "synthetic_fixture_only": registry.get("synthetic_fixture_only"),
        "fixture_path": _as_posix(fixture_path),
        "fixture_contains_only_synthetic_entries": fixture_contains_only_synthetic_entries(
            fixture
        ),
        "real_urls_present": artifact_findings.get("real_urls_present", False),
        "real_source_claims_present": artifact_findings.get(
            "real_source_claims_present", False
        ),
        "secrets_present": artifact_findings.get("secrets_present", False),
        "external_repo_commands_present": artifact_findings.get(
            "external_repo_commands_present", False
        ),
        "source_retrieval_created": _flag_from_registry(
            registry, "retrieves_source_facts"
        ),
        "source_acceptance_created": _flag_from_registry(
            registry, "accepts_source_facts"
        ),
        "accepted_source_packets_created": _flag_from_registry(
            registry, "creates_accepted_source_packets"
        ),
        "connector_semantics_created": _flag_from_registry(
            registry, "creates_connector_semantics"
        ),
        "runtime_artifacts_created": _flag_from_registry(
            registry, "creates_runtime_artifacts"
        ),
        "runtime_receipts_created": _mapping(
            registry.get("forbidden_artifact_flags")
        ).get("runtime_receipts")
        is True,
        "live_receipts_created": _mapping(
            registry.get("forbidden_artifact_flags")
        ).get("live_receipts")
        is True,
        "order_receipts_created": _mapping(
            registry.get("forbidden_artifact_flags")
        ).get("order_receipts")
        is True,
        "cash_receipts_created": _mapping(
            registry.get("forbidden_artifact_flags")
        ).get("cash_receipts")
        is True,
        "replay_results_created": _flag_from_registry(
            registry, "creates_replay_results"
        ),
        "paper_results_created": _flag_from_registry(registry, "creates_paper_results"),
        "live_readiness_created": _flag_from_registry(
            registry, "creates_live_readiness"
        ),
        "order_authority_created": _flag_from_registry(
            registry, "creates_order_authority"
        ),
        "profit_evidence_created": _flag_from_registry(
            registry, "creates_profit_evidence"
        ),
        "quantum_backend_evidence_created": _flag_from_registry(
            registry, "creates_quantum_backend_evidence"
        ),
        "quantum_advantage_claim_created": _flag_from_registry(
            registry, "creates_quantum_advantage_claim"
        ),
        "latency_superiority_claim_created": _flag_from_registry(
            registry, "creates_latency_superiority_claim"
        ),
        "execution_superiority_claim_created": _flag_from_registry(
            registry, "creates_execution_superiority_claim"
        ),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "pr72_conversion_implemented": _flag_from_registry(
            registry, "implements_pr72_conversion"
        ),
        "candidate_parameter_family_packet_created": _flag_from_registry(
            registry, "candidate_parameter_family_packet_created"
        ),
        "candidate_algorithm_family_packet_created": _flag_from_registry(
            registry, "candidate_algorithm_family_packet_created"
        ),
        "candidate_agent_binding_request_created": _flag_from_registry(
            registry, "candidate_agent_binding_request_created"
        ),
        "owner_override_receipt_reference_created": _flag_from_registry(
            registry, "owner_override_receipt_reference_created"
        ),
        "owner_override_supported": registry.get("owner_override_supported"),
        "owner_override_satisfies_internal_workflow_only": registry.get(
            "owner_override_satisfies_internal_workflow_only"
        ),
        "random_selection_implemented": _flag_from_registry(
            registry, "implements_random_selection"
        ),
        "ranking_implemented": _flag_from_registry(registry, "implements_ranking"),
        "scoring_implemented": _flag_from_registry(registry, "implements_scoring"),
        "arbitration_implemented": _flag_from_registry(
            registry, "implements_arbitration"
        ),
        "trade_context_routing_implemented": _flag_from_registry(
            registry, "implements_trade_context_routing"
        ),
        "stack_selection_implemented": _flag_from_registry(
            registry, "implements_stack_selection"
        ),
        "quantum_classical_arbitration_implemented": _flag_from_registry(
            registry, "implements_quantum_classical_arbitration"
        ),
        "final_ready": registry.get("final_ready"),
        "validation_marker": SUCCESS_MARKER,
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "depends_on_pr70_classifier": True,
        "pr70_source_type_count_observed": len(CANONICAL_SOURCE_TYPES),
        "supported_source_type_count": len(CANONICAL_SOURCE_TYPES),
        "roadmap_required_entry_field_count": len(ROADMAP_REQUIRED_ENTRY_FIELDS),
        "quantum_forward_entry_field_count": len(QUANTUM_FORWARD_ENTRY_FIELDS),
        "required_entry_fields_present": True,
        "quantum_forward_fields_present": True,
        "production_intake_entries_count": 0,
        "real_owner_intake_entry_count": 0,
        "real_owner_intakes_invented": False,
        "synthetic_fixture_only": True,
        "fixture_contains_only_synthetic_entries": True,
        "owner_override_supported": True,
        "owner_override_satisfies_internal_workflow_only": True,
        "random_selection_implemented": False,
        "ranking_implemented": False,
        "scoring_implemented": False,
        "arbitration_implemented": False,
        "trade_context_routing_implemented": False,
        "stack_selection_implemented": False,
        "quantum_classical_arbitration_implemented": False,
        "final_ready": False,
        "validation_marker": SUCCESS_MARKER,
    }
    for field in REPORT_FALSE_FIELDS:
        expected_values[field] = False
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is not deterministic JSON")
    return failures


def _read_text_if_exists(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
    pr70_schema_path: pathlib.Path = DEFAULT_PR70_SCHEMA,
    pr70_registry_path: pathlib.Path = DEFAULT_PR70_REGISTRY,
    pr70_report_path: pathlib.Path = DEFAULT_PR70_REPORT,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    pr70_source_types, pr70_failures = validate_pr70_dependency(
        repo_root=root,
        pr70_schema_path=pr70_schema_path,
        pr70_registry_path=pr70_registry_path,
        pr70_report_path=pr70_report_path,
    )
    failures.extend(pr70_failures)

    try:
        registry = load_registry(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    try:
        fixture = load_fixture(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    schema, schema_failures = _load_json_checked(root / schema_path)
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(
            validate_schema_surface(schema, pr70_source_types=pr70_source_types)
        )
        failures.extend(validate_json_schema_subset(registry, schema))
        failures.extend(
            validate_fixture_payload(
                fixture,
                schema=schema,
                pr70_source_types=pr70_source_types,
            )
        )

    failures.extend(
        validate_registry_payload(
            registry,
            label="production_registry",
            pr70_source_types=pr70_source_types,
            production=True,
            synthetic_only_entries=False,
        )
    )

    artifact_texts = (
        (_as_posix(schema_path), _read_text_if_exists(root / schema_path)),
        (_as_posix(registry_path), _read_text_if_exists(root / registry_path)),
        (_as_posix(fixture_path), _read_text_if_exists(root / fixture_path)),
    )
    artifact_findings = forbidden_text_findings(artifact_texts)
    failures.extend(validate_no_forbidden_artifact_text(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))

    report = build_report(
        repo_root=root,
        registry=registry,
        fixture=fixture,
        pr70_source_types=pr70_source_types,
        artifact_findings=artifact_findings,
        pr70_report_path=pr70_report_path,
        production_registry_path=registry_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        repo_root=root,
        registry=registry,
        fixture=fixture,
        pr70_source_types=pr70_source_types,
        artifact_findings=artifact_findings,
        pr70_report_path=pr70_report_path,
        production_registry_path=registry_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated owner intake registry report is not deterministic")
    report_text = serialize_report(report)
    failures.extend(validate_no_forbidden_artifact_text((("generated_report", report_text),)))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: owner-submitted source intake registry is "
            "static intake metadata only"
        )

    if output_path is not None and not failures:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dev", choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--pr70-schema", default=str(DEFAULT_PR70_SCHEMA))
    parser.add_argument("--pr70-registry", default=str(DEFAULT_PR70_REGISTRY))
    parser.add_argument("--pr70-report", default=str(DEFAULT_PR70_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
        pr70_schema_path=pathlib.Path(args.pr70_schema),
        pr70_registry_path=pathlib.Path(args.pr70_registry),
        pr70_report_path=pathlib.Path(args.pr70_report),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(marker)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
