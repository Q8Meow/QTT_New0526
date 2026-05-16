#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
    / "atomicrows"
    / "atomicrows_parameter_stack_completeness_gate.schema.json"
)
DEFAULT_PRODUCTION_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompletenessGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_stack_completeness_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompletenessGate.report.json"
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
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = (
    pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
)

GATE_ID = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE"
GATE_VERSION = "v1"
REPORT_ID = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_atomicrows_parameter_stack_completeness_gate.py"
AUTHORITY_CLASS = (
    "STATIC_PARAMETER_STACK_COMPLETENESS_GATE_NOT_STACK_COMPATIBILITY_NOT_STACK_"
    "SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_STACK_COMPATIBILITY_NOT_STACK_SELECTION_NOT_"
    "SCORING_NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_FAILED"
OWNER_OVERRIDE_INTERNAL_ONLY = (
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_STACK_READINESS_ONLY"
)
OWNER_GLOBAL_OVERRIDE = "OWNER_GLOBAL_OVERRIDE"

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
ROLE_COMPLETION_STATES = (
    "ROLE_COMPLETE",
    "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE",
    "ROLE_INCOMPLETE_DUPLICATE_ROLE",
    "ROLE_INCOMPLETE_SINGLE_PARAMETER_ONLY",
    "ROLE_INCOMPLETE_SINGLE_ALGORITHM_ONLY",
    OWNER_OVERRIDE_INTERNAL_ONLY,
    "SYNTHETIC_FIXTURE_ONLY_NOT_PRODUCTION_READY",
)
SCHEMA_REQUIRED_FIELDS = (
    "gate_id",
    "gate_version",
    "authority_class",
    "depends_on_parameter_stack_role_taxonomy",
    "required_stack_roles",
    "completeness_cases",
    "completeness_policy",
    "owner_override_policy",
    "quantum_advisory_policy",
    "future_consumer_contract",
    "forbidden_artifact_flags",
    "validation_invariants",
    "final_ready",
)
COMPLETENESS_CASE_REQUIRED_FIELDS = (
    "stack_case_id",
    "stack_case_type",
    "supplied_role_ids",
    "missing_role_ids",
    "duplicate_role_ids",
    "role_completion_state",
    "normal_stack_readiness",
    "owner_override_present",
    "owner_override_satisfaction_basis",
    "owner_override_stack_readiness",
    "final_stack_readiness",
    "single_parameter_set",
    "single_algorithm_set",
    "completeness_authority_class",
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "deterministic_trace",
    "no_claim_flags",
)
REQUIRED_CASE_IDS = (
    "SYNTHETIC_ALL_NINE_REQUIRED_ROLES_PRESENT",
    "SYNTHETIC_MISSING_SIGNAL_BLOCKS_NORMAL_READINESS",
    "SYNTHETIC_MISSING_QUANTUM_ADVISORY_BLOCKS_NORMAL_COMPLETENESS",
    "SYNTHETIC_DUPLICATE_SIGNAL_BLOCKS_NORMAL_READINESS",
    "SYNTHETIC_SINGLE_PARAMETER_SET_WITHOUT_OWNER_OVERRIDE",
    "SYNTHETIC_SINGLE_ALGORITHM_SET_WITHOUT_OWNER_OVERRIDE",
    "SYNTHETIC_MISSING_RISK_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_SINGLE_PARAMETER_SET_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_SINGLE_ALGORITHM_SET_WITH_OWNER_GLOBAL_OVERRIDE",
)
NO_CLAIM_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "runtime_artifacts_created",
    "live_readiness_created",
    "order_authority_created",
    "cash_receipts_created",
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
    "ranking_created",
    "scoring_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "stack_selection_created",
    "stack_compatibility_gate_created",
    "runtime_live_use_created",
)
EXPLICIT_NO_CLAIM_FIELDS = (
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_packets",
    "creates_connector_semantics",
    "creates_runtime_artifacts",
    "creates_atomicrows_bundle_rows",
    "creates_atomicrows_bundle_jsonl",
    "creates_atomicrows_bundle_sha256",
    "creates_replay_results",
    "creates_paper_results",
    "creates_live_readiness",
    "creates_order_authority",
    "creates_cash_receipts",
    "creates_profit_evidence",
    "creates_quantum_backend_evidence",
    "creates_quantum_advantage_claim",
    "creates_latency_superiority_claim",
    "creates_execution_superiority_claim",
    "creates_ranking",
    "creates_scoring",
    "creates_optimizer_arbitration",
    "creates_trade_context_routing",
    "creates_stack_selection",
    "creates_stack_compatibility_gate",
    "creates_runtime_or_live_trading_authority",
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
QUANTUM_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_scoring_created",
    "quantum_arbitration_created",
)
CASE_FALSE_FIELDS = (
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "final_stack_readiness",
)
REPORT_FALSE_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "runtime_artifacts_created",
    "live_readiness_created",
    "order_authority_created",
    "cash_receipts_created",
    "replay_results_created",
    "paper_results_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "ranking_created",
    "scoring_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "stack_selection_created",
    "stack_compatibility_gate_created",
    "atomicrows_bundle_sha256_exists",
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
    "single_parameter_set_complete_without_owner_override",
    "single_algorithm_set_complete_without_owner_override",
    "production_stack_completeness_evaluated",
    "production_stack_ready",
    "final_ready",
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


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


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
        ("ORDER_COMMAND_SUBMIT", "submit" + " order"),
        ("ORDER_COMMAND_CANCEL", "cancel" + " order"),
        ("ORDER_COMMAND_REPLACE", "replace" + " order"),
        ("SOURCE_ACCEPTANCE_CLAIM", "accepted source packet" + " created"),
        ("CONNECTOR_SEMANTIC_CLAIM", "connector semantic binding" + " created"),
        ("RUNTIME_AUTHORITY_CLAIM", "runtime authority" + " created"),
        ("REPLAY_PROOF_CLAIM", "replay passed" + " as proof"),
        ("PAPER_PROOF_CLAIM", "paper passed" + " as proof"),
        ("PROFIT_CLAIM", "profit" + " proven"),
        ("QUANTUM_BACKEND_EXECUTION_CLAIM", "backend" + " executed"),
        ("QUANTUM_ADVANTAGE_CLAIM", "quantum advantage" + " proven"),
        ("BUNDLE_JSONL_CREATION_CLAIM", "AtomicRows.bundle.jsonl" + " created"),
        ("BUNDLE_SHA_CREATION_CLAIM", "AtomicRows.bundle.sha256" + " created"),
        ("RANKED_BEST_STACK_CLAIM", "ranked" + " best stack"),
        ("SELECTED_BEST_STACK_CLAIM", "selected" + " best stack"),
        ("OPTIMIZER_ARBITRATION_RESULT_CLAIM", "optimizer arbitration" + " result"),
        ("TRADE_ROUTED_CLAIM", "trade" + " routed"),
        ("LIVE_ELIGIBLE_CLAIM", "live" + " eligible"),
    )


def _forbidden_text_regexes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    return (
        ("SECRET_LIKE_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("ORDER_FILL_CLAIM", re.compile(r"\bfills\b", re.IGNORECASE)),
    )


def validate_no_forbidden_claims(texts: Sequence[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    for label, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() in lowered:
                failures.append(f"{label}: forbidden fixture or gate text {code}")
        for code, pattern in _forbidden_text_regexes():
            if pattern.search(text):
                failures.append(f"{label}: forbidden fixture or gate text {code}")
    return failures


def validate_pr73_dependency(root: pathlib.Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    paths = (
        ("PR73_ROLE_TAXONOMY_SCHEMA", PR73_SCHEMA),
        ("PR73_ROLE_TAXONOMY_REGISTRY", PR73_REGISTRY),
        ("PR73_ROLE_TAXONOMY_REPORT", PR73_REPORT),
    )
    for label, rel_path in paths:
        if not (root / rel_path).exists():
            failures.append(f"PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: {label} missing")

    if failures:
        return list(REQUIRED_STACK_ROLES), failures

    pr73_schema = load_json(root / PR73_SCHEMA)
    pr73_registry = load_yaml(root / PR73_REGISTRY)
    pr73_report = load_json(root / PR73_REPORT)
    roles = pr73_registry.get("required_stack_roles")
    if roles != list(REQUIRED_STACK_ROLES):
        failures.append("PR73 required_stack_roles do not match canonical PR74 order")
    schema_roles = _mapping(pr73_schema.get("properties")).get("required_stack_roles")
    if _mapping(schema_roles).get("const") != list(REQUIRED_STACK_ROLES):
        failures.append("PR73 schema required_stack_roles const mismatch")
    if pr73_report.get("validation_marker") != "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK":
        failures.append("PR73 report validation marker missing")
    if pr73_report.get("required_stack_roles_order_valid") is not True:
        failures.append("PR73 report required_stack_roles_order_valid must be true")
    return list(roles if isinstance(roles, list) else REQUIRED_STACK_ROLES), failures


def validate_required_roles(
    payload: dict[str, Any],
    expected_roles: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    roles = payload.get("required_stack_roles")
    if roles != list(expected_roles):
        failures.append(f"{label}.required_stack_roles must match PR73 canonical order")
    if len(roles if isinstance(roles, list) else []) != len(REQUIRED_STACK_ROLES):
        failures.append(f"{label}.required_stack_roles must contain nine roles")
    unknown = sorted(set(roles if isinstance(roles, list) else []) - set(expected_roles))
    if unknown:
        failures.append(f"{label}.required_stack_roles unknown role IDs: {unknown}")
    if "QUANTUM_ADVISORY" not in (roles if isinstance(roles, list) else []):
        failures.append(f"{label}.required_stack_roles missing QUANTUM_ADVISORY")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["PR74 schema root required must be a list"]
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR74 schema missing required root field {field}")

    defs = _mapping(schema.get("$defs"))
    case_schema = _mapping(defs.get("completeness_case"))
    case_required = case_schema.get("required")
    if not isinstance(case_required, list):
        failures.append("PR74 schema completeness_case required must be a list")
    else:
        for field in COMPLETENESS_CASE_REQUIRED_FIELDS:
            if field not in case_required:
                failures.append(
                    f"PR74 schema completeness_case missing required field {field}"
                )
    state_enum = (
        _mapping(_mapping(case_schema.get("properties")).get("role_completion_state"))
        .get("enum")
    )
    if state_enum != list(ROLE_COMPLETION_STATES):
        failures.append("PR74 schema role_completion_state enum mismatch")
    no_claim_required = _mapping(defs.get("no_claim_flags")).get("required")
    if no_claim_required != list(NO_CLAIM_FIELDS):
        failures.append("PR74 schema no_claim_flags required field order mismatch")
    return failures


def _schema_subset_failures(
    payload: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> list[str]:
    return [
        f"{label}{failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def validate_owner_override_policy(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("owner_override_policy"))
    if policy.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_supported must be true")
    if policy.get("owner_override_satisfies_internal_stack_readiness_only") is not True:
        failures.append(
            f"{label}.owner_override_satisfies_internal_stack_readiness_only must be true"
        )
    for field in OWNER_OVERRIDE_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_quantum_advisory_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("quantum_advisory_policy"))
    true_fields = (
        "quantum_advisory_role_required_for_normal_completeness",
        "missing_quantum_advisory_blocks_normal_completeness",
        "quantum_advisory_is_static_completeness_role_only",
        "future_quantum_applicability_registry_required_before_quantum_selection",
        "replay_paper_evidence_required_before_advantage_claim",
        "live_evidence_required_before_profit_claim",
    )
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in QUANTUM_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_no_forbidden_claim_flags(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for field in EXPLICIT_NO_CLAIM_FIELDS:
        if _mapping(payload.get("explicit_no_claim_flags")).get(field) is not False:
            failures.append(f"{label}.explicit_no_claim_flags.{field} must be false")
    for field in NO_CLAIM_FIELDS:
        if _mapping(payload.get("forbidden_artifact_flags")).get(field) is not False:
            failures.append(f"{label}.forbidden_artifact_flags.{field} must be false")
    for case in _list_of_mappings(payload.get("completeness_cases")):
        case_id = str(case.get("stack_case_id"))
        flags = _mapping(case.get("no_claim_flags"))
        for field in NO_CLAIM_FIELDS:
            if flags.get(field) is not False:
                failures.append(f"{label}.{case_id}.no_claim_flags.{field} must be false")
    return failures


def validate_production_gate(
    production_gate: dict[str, Any],
    schema: dict[str, Any],
    pr73_roles: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    failures.extend(_schema_subset_failures(production_gate, schema, "production_gate"))
    failures.extend(validate_required_roles(production_gate, pr73_roles, "production_gate"))
    if production_gate.get("gate_id") != GATE_ID:
        failures.append("production_gate.gate_id mismatch")
    if production_gate.get("gate_version") != GATE_VERSION:
        failures.append("production_gate.gate_version mismatch")
    if production_gate.get("authority_class") != AUTHORITY_CLASS:
        failures.append("production_gate.authority_class mismatch")
    readiness = _mapping(production_gate.get("production_readiness"))
    expected_readiness = {
        "completeness_gate_contract_ready": True,
        "production_complete_stack_count": 0,
        "production_incomplete_stack_count": 0,
        "production_owner_override_satisfied_stack_count": 0,
        "production_stack_completeness_evaluated": False,
        "production_stack_ready": False,
        "final_ready": False,
    }
    for field, expected in expected_readiness.items():
        if readiness.get(field) != expected:
            failures.append(f"production_gate.production_readiness.{field} mismatch")
    policy = _mapping(production_gate.get("completeness_policy"))
    if policy.get("all_required_roles_required_for_normal_completeness") is not True:
        failures.append("all required roles policy must be true")
    if policy.get("missing_required_role_blocks_normal_stack_readiness") is not True:
        failures.append("missing required role block policy must be true")
    if policy.get("duplicate_role_ids_block_normal_stack_readiness") is not True:
        failures.append("duplicate role block policy must be true")
    if policy.get("single_parameter_set_complete_without_owner_override") is not False:
        failures.append("single parameter without owner override must be false")
    if policy.get("single_algorithm_set_complete_without_owner_override") is not False:
        failures.append("single algorithm without owner override must be false")
    if policy.get("owner_override_may_satisfy_internal_stack_readiness") is not True:
        failures.append("owner override internal readiness policy must be true")
    if policy.get("final_ready_created_by_this_gate") is not False:
        failures.append("final ready created by this gate must be false")
    if production_gate.get("final_ready") is not False:
        failures.append("production_gate.final_ready must be false")
    failures.extend(validate_owner_override_policy(production_gate, "production_gate"))
    failures.extend(validate_quantum_advisory_boundary(production_gate, "production_gate"))
    failures.extend(validate_no_forbidden_claim_flags(production_gate, "production_gate"))
    return failures


def _duplicate_role_ids(role_ids: Sequence[str]) -> list[str]:
    counts = Counter(role_ids)
    return [role for role in REQUIRED_STACK_ROLES if counts[role] > 1]


def _missing_role_ids(role_ids: Sequence[str]) -> list[str]:
    supplied = set(role_ids)
    return [role for role in REQUIRED_STACK_ROLES if role not in supplied]


def _case_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("stack_case_id")): case
        for case in _list_of_mappings(fixture.get("completeness_cases"))
    }


def _case_role_failures(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    case_id = str(case.get("stack_case_id"))
    supplied = case.get("supplied_role_ids")
    if not isinstance(supplied, list):
        return [f"{case_id}.supplied_role_ids must be a list"]
    unknown = sorted(set(supplied) - set(REQUIRED_STACK_ROLES))
    if unknown:
        failures.append(f"{case_id}.supplied_role_ids unknown role IDs: {unknown}")
    expected_missing = _missing_role_ids([str(role) for role in supplied])
    expected_duplicates = _duplicate_role_ids([str(role) for role in supplied])
    if case.get("missing_role_ids") != expected_missing:
        failures.append(f"{case_id}.missing_role_ids mismatch")
    if case.get("duplicate_role_ids") != expected_duplicates:
        failures.append(f"{case_id}.duplicate_role_ids mismatch")
    trace = _mapping(case.get("deterministic_trace"))
    if trace.get("expected_missing_role_ids") != expected_missing:
        failures.append(f"{case_id}.deterministic_trace expected_missing mismatch")
    if trace.get("expected_duplicate_role_ids") != expected_duplicates:
        failures.append(f"{case_id}.deterministic_trace expected_duplicate mismatch")
    return failures


def _case_common_failures(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    case_id = str(case.get("stack_case_id"))
    for field in CASE_FALSE_FIELDS:
        if case.get(field) is not False:
            failures.append(f"{case_id}.{field} must be false")
    trace = _mapping(case.get("deterministic_trace"))
    for field in (
        "random_selection_used",
        "ranking_used",
        "scoring_used",
        "optimizer_arbitration_used",
        "trade_context_routing_used",
        "stack_selection_used",
        "runtime_evaluation_used",
    ):
        if trace.get(field) is not False:
            failures.append(f"{case_id}.deterministic_trace.{field} must be false")
    return failures


def validate_fixture_cases(
    fixture: dict[str, Any],
    schema: dict[str, Any],
    pr73_roles: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    failures.extend(_schema_subset_failures(fixture, schema, "fixture"))
    failures.extend(validate_required_roles(fixture, pr73_roles, "fixture"))
    if fixture.get("fixture_id") != "SYNTHETIC_ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_FIXTURE":
        failures.append("fixture.fixture_id mismatch")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")

    cases = _case_by_id(fixture)
    if list(cases) != list(REQUIRED_CASE_IDS):
        failures.append("fixture completeness case order or IDs mismatch")
    for case in cases.values():
        failures.extend(_case_role_failures(case))
        failures.extend(_case_common_failures(case))

    full = _mapping(cases.get("SYNTHETIC_ALL_NINE_REQUIRED_ROLES_PRESENT"))
    if full.get("supplied_role_ids") != list(REQUIRED_STACK_ROLES):
        failures.append("full-role case supplied_role_ids must match canonical order")
    if full.get("role_completion_state") != "ROLE_COMPLETE":
        failures.append("full-role case must be ROLE_COMPLETE")
    if full.get("normal_stack_readiness") != "NORMAL_STACK_READY":
        failures.append("full-role case must have normal stack readiness")

    missing_signal = _mapping(cases.get("SYNTHETIC_MISSING_SIGNAL_BLOCKS_NORMAL_READINESS"))
    if missing_signal.get("missing_role_ids") != ["SIGNAL"]:
        failures.append("missing SIGNAL case must identify SIGNAL")
    if missing_signal.get("role_completion_state") != "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE":
        failures.append("missing SIGNAL case must be missing-role incomplete")
    if missing_signal.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
        failures.append("missing SIGNAL case must block normal readiness")

    missing_quantum = _mapping(
        cases.get("SYNTHETIC_MISSING_QUANTUM_ADVISORY_BLOCKS_NORMAL_COMPLETENESS")
    )
    if missing_quantum.get("missing_role_ids") != ["QUANTUM_ADVISORY"]:
        failures.append("missing QUANTUM_ADVISORY case must identify QUANTUM_ADVISORY")
    if missing_quantum.get("role_completion_state") != "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE":
        failures.append("missing QUANTUM_ADVISORY case must be missing-role incomplete")
    if missing_quantum.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
        failures.append("missing QUANTUM_ADVISORY case must block normal completeness")

    duplicate = _mapping(cases.get("SYNTHETIC_DUPLICATE_SIGNAL_BLOCKS_NORMAL_READINESS"))
    if duplicate.get("duplicate_role_ids") != ["SIGNAL"]:
        failures.append("duplicate role case must identify duplicate SIGNAL")
    if duplicate.get("role_completion_state") != "ROLE_INCOMPLETE_DUPLICATE_ROLE":
        failures.append("duplicate role case must be duplicate-role incomplete")
    if duplicate.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
        failures.append("duplicate role case must block normal readiness")

    single_parameter = _mapping(
        cases.get("SYNTHETIC_SINGLE_PARAMETER_SET_WITHOUT_OWNER_OVERRIDE")
    )
    if single_parameter.get("single_parameter_set") is not True:
        failures.append("single-parameter case must set single_parameter_set true")
    if single_parameter.get("owner_override_present") is not False:
        failures.append("single-parameter no-override case must not contain override")
    if single_parameter.get("role_completion_state") != "ROLE_INCOMPLETE_SINGLE_PARAMETER_ONLY":
        failures.append("single-parameter no-override case must be incomplete")
    if single_parameter.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
        failures.append("single-parameter no-override case must block normal readiness")

    single_algorithm = _mapping(
        cases.get("SYNTHETIC_SINGLE_ALGORITHM_SET_WITHOUT_OWNER_OVERRIDE")
    )
    if single_algorithm.get("single_algorithm_set") is not True:
        failures.append("single-algorithm case must set single_algorithm_set true")
    if single_algorithm.get("owner_override_present") is not False:
        failures.append("single-algorithm no-override case must not contain override")
    if single_algorithm.get("role_completion_state") != "ROLE_INCOMPLETE_SINGLE_ALGORITHM_ONLY":
        failures.append("single-algorithm no-override case must be incomplete")
    if single_algorithm.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
        failures.append("single-algorithm no-override case must block normal readiness")

    override_ids = (
        "SYNTHETIC_MISSING_RISK_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SINGLE_PARAMETER_SET_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SINGLE_ALGORITHM_SET_WITH_OWNER_GLOBAL_OVERRIDE",
    )
    for case_id in override_ids:
        case = _mapping(cases.get(case_id))
        if case.get("owner_override_present") is not True:
            failures.append(f"{case_id} owner override must be present")
        if case.get("owner_override_satisfaction_basis") != OWNER_GLOBAL_OVERRIDE:
            failures.append(f"{case_id} owner override basis must be OWNER_GLOBAL_OVERRIDE")
        if case.get("role_completion_state") != OWNER_OVERRIDE_INTERNAL_ONLY:
            failures.append(f"{case_id} must satisfy internal stack readiness only")
        if (
            case.get("owner_override_stack_readiness")
            != "OWNER_OVERRIDE_INTERNAL_STACK_READINESS_SATISFIED"
        ):
            failures.append(f"{case_id} owner override stack readiness mismatch")
        if case.get("normal_stack_readiness") != "NORMAL_STACK_BLOCKED":
            failures.append(f"{case_id} normal readiness must remain blocked")
    failures.extend(validate_owner_override_policy(fixture, "fixture"))
    failures.extend(validate_quantum_advisory_boundary(fixture, "fixture"))
    failures.extend(validate_no_forbidden_claim_flags(fixture, "fixture"))
    return failures


def validate_no_forbidden_artifacts(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
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
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR74"]
    stderr = completed.stderr.strip()
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {stderr}"]


def _flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("explicit_no_claim_flags")).get(field))


def _forbidden_flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("forbidden_artifact_flags")).get(field))


def _owner_flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("owner_override_policy")).get(field))


def _quantum_flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("quantum_advisory_policy")).get(field))


def _case(payload: dict[str, Any], case_id: str) -> dict[str, Any]:
    return _mapping(_case_by_id(payload).get(case_id))


def build_report(
    *,
    root: pathlib.Path,
    production_gate: dict[str, Any],
    fixture: dict[str, Any],
    schema_path: pathlib.Path,
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    readiness = _mapping(production_gate.get("production_readiness"))
    full_case = _case(fixture, "SYNTHETIC_ALL_NINE_REQUIRED_ROLES_PRESENT")
    missing_signal = _case(fixture, "SYNTHETIC_MISSING_SIGNAL_BLOCKS_NORMAL_READINESS")
    missing_quantum = _case(
        fixture,
        "SYNTHETIC_MISSING_QUANTUM_ADVISORY_BLOCKS_NORMAL_COMPLETENESS",
    )
    duplicate = _case(fixture, "SYNTHETIC_DUPLICATE_SIGNAL_BLOCKS_NORMAL_READINESS")
    return {
        "accepted_source_packets_created": _flag(
            production_gate, "creates_accepted_source_packets"
        ),
        "all_required_roles_case_complete": (
            full_case.get("role_completion_state") == "ROLE_COMPLETE"
            and full_case.get("normal_stack_readiness") == "NORMAL_STACK_READY"
        ),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "cash_receipts_created": _flag(production_gate, "creates_cash_receipts"),
        "completeness_gate_contract_ready": readiness.get(
            "completeness_gate_contract_ready"
        ),
        "connector_semantics_created": _flag(
            production_gate, "creates_connector_semantics"
        ),
        "depends_on_pr73_role_taxonomy": True,
        "duplicate_role_blocks_normal_stack_readiness": (
            duplicate.get("role_completion_state") == "ROLE_INCOMPLETE_DUPLICATE_ROLE"
            and duplicate.get("normal_stack_readiness") == "NORMAL_STACK_BLOCKED"
        ),
        "execution_superiority_claim_created": _flag(
            production_gate, "creates_execution_superiority_claim"
        ),
        "final_ready": production_gate.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "latency_superiority_claim_created": _flag(
            production_gate, "creates_latency_superiority_claim"
        ),
        "live_readiness_created": _flag(production_gate, "creates_live_readiness"),
        "missing_quantum_advisory_blocks_normal_completeness": (
            missing_quantum.get("missing_role_ids") == ["QUANTUM_ADVISORY"]
            and missing_quantum.get("normal_stack_readiness") == "NORMAL_STACK_BLOCKED"
        ),
        "missing_role_blocks_normal_stack_readiness": (
            missing_signal.get("missing_role_ids") == ["SIGNAL"]
            and missing_signal.get("normal_stack_readiness") == "NORMAL_STACK_BLOCKED"
        ),
        "optimizer_arbitration_created": _flag(
            production_gate, "creates_optimizer_arbitration"
        ),
        "order_authority_created": _flag(production_gate, "creates_order_authority"),
        "owner_override_fabricates_accepted_source_packet": _owner_flag(
            production_gate, "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_connector_semantic": _owner_flag(
            production_gate, "owner_override_fabricates_connector_semantic"
        ),
        "owner_override_fabricates_external_fact": _owner_flag(
            production_gate, "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": _owner_flag(
            production_gate, "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": _owner_flag(
            production_gate, "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": _owner_flag(
            production_gate, "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": _owner_flag(
            production_gate, "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": _owner_flag(
            production_gate, "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_satisfies_internal_stack_readiness_only": _owner_flag(
            production_gate, "owner_override_satisfies_internal_stack_readiness_only"
        ),
        "paper_results_created": _flag(production_gate, "creates_paper_results"),
        "production_gate_path": _as_posix(production_gate_path),
        "production_stack_completeness_evaluated": readiness.get(
            "production_stack_completeness_evaluated"
        ),
        "production_stack_ready": readiness.get("production_stack_ready"),
        "profit_evidence_created": _flag(production_gate, "creates_profit_evidence"),
        "quantum_advantage_claim_created": _quantum_flag(
            production_gate, "quantum_advantage_claim_created"
        ) or _flag(production_gate, "creates_quantum_advantage_claim"),
        "quantum_backend_evidence_created": _flag(
            production_gate, "creates_quantum_backend_evidence"
        ),
        "ranking_created": _flag(production_gate, "creates_ranking"),
        "replay_results_created": _flag(production_gate, "creates_replay_results"),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_stack_role_count": len(production_gate.get("required_stack_roles", [])),
        "required_stack_roles_order_valid": production_gate.get("required_stack_roles")
        == list(REQUIRED_STACK_ROLES),
        "runtime_artifacts_created": _flag(production_gate, "creates_runtime_artifacts"),
        "schema_path": _as_posix(schema_path),
        "scoring_created": _flag(production_gate, "creates_scoring"),
        "single_algorithm_set_complete_without_owner_override": _mapping(
            production_gate.get("completeness_policy")
        ).get("single_algorithm_set_complete_without_owner_override"),
        "single_parameter_set_complete_without_owner_override": _mapping(
            production_gate.get("completeness_policy")
        ).get("single_parameter_set_complete_without_owner_override"),
        "source_acceptance_created": _flag(production_gate, "accepts_source_facts"),
        "source_retrieval_created": _flag(production_gate, "retrieves_source_facts"),
        "stack_compatibility_gate_created": _forbidden_flag(
            production_gate, "stack_compatibility_gate_created"
        )
        or _flag(production_gate, "creates_stack_compatibility_gate"),
        "stack_selection_created": _flag(production_gate, "creates_stack_selection"),
        "trade_context_routing_created": _flag(
            production_gate, "creates_trade_context_routing"
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
        "required_stack_role_count": len(REQUIRED_STACK_ROLES),
        "required_stack_roles_order_valid": True,
        "completeness_gate_contract_ready": True,
        "all_required_roles_case_complete": True,
        "missing_role_blocks_normal_stack_readiness": True,
        "missing_quantum_advisory_blocks_normal_completeness": True,
        "duplicate_role_blocks_normal_stack_readiness": True,
        "owner_override_satisfies_internal_stack_readiness_only": True,
        "validation_marker": SUCCESS_MARKER,
    }
    for field in REPORT_FALSE_FIELDS:
        expected_values[field] = False
    if not isinstance(report.get("atomicrows_bundle_jsonl_exists"), bool):
        failures.append("report.atomicrows_bundle_jsonl_exists must be boolean")
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
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    pr73_roles, pr73_failures = validate_pr73_dependency(root)
    failures.extend(pr73_failures)

    schema, schema_failures = _load_json_checked(root / schema_path, "PR74_SCHEMA")
    failures.extend(schema_failures)
    if schema:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_gate = load_yaml(root / production_gate_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(failures=(f"PR74_PRODUCTION_GATE_MALFORMED: {exc}",), report=None)
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(failures=(f"PR74_FIXTURE_MALFORMED: {exc}",), report=None)

    if schema:
        failures.extend(validate_production_gate(production_gate, schema, pr73_roles))
        failures.extend(validate_fixture_cases(fixture, schema, pr73_roles))
    else:
        failures.extend(validate_required_roles(production_gate, pr73_roles, "production_gate"))
        failures.extend(validate_required_roles(fixture, pr73_roles, "fixture"))

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_gate_path), _read_text(root / production_gate_path)),
        (_as_posix(fixture_path), _read_text(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        production_gate=production_gate,
        fixture=fixture,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        production_gate=production_gate,
        fixture=fixture,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR74 report is not deterministic")
    failures.extend(validate_no_forbidden_claims((("generated_report", serialize_report(report)),)))
    failures.extend(_report_safety_failures(report))

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-gate", default=str(DEFAULT_PRODUCTION_GATE))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_gate_path=pathlib.Path(args.production_gate),
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
