#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    / "atomicrows_parameter_stack_role_taxonomy.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackRoleTaxonomy.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_stack_role_taxonomy.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackRoleTaxonomy.report.json"
)
PR70_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_research_provenance_evidence_tier_classification.schema.json"
)
PR70_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsResearchProvenanceEvidenceTierClassification.yaml"
)
PR70_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
)
PR71_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_owner_submitted_research_source_intake_registry.schema.json"
)
PR71_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.yaml"
)
PR71_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
)
PR72_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_research_source_to_candidate_family_gate.schema.json"
)
PR72_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsResearchSourceToCandidateFamilyGate.yaml"
)
PR72_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
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

REGISTRY_ID = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY"
REGISTRY_VERSION = "v1"
REPORT_ID = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_atomicrows_parameter_stack_role_taxonomy.py"
AUTHORITY_CLASS = (
    "STATIC_PARAMETER_STACK_ROLE_TAXONOMY_NOT_STACK_COMPLETENESS_NOT_STACK_"
    "COMPATIBILITY_NOT_STACK_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_STACK_COMPLETENESS_NOT_STACK_COMPATIBILITY_"
    "NOT_STACK_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_FAILED"
FINAL_INCOMPLETE_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_FINAL_INCOMPLETE"
OWNER_OVERRIDE_INTERNAL_ONLY = "OWNER_OVERRIDE_SATISFIED_INTERNAL_STACK_READINESS_ONLY"

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
ROLE_INSTITUTIONAL_PURPOSES = {
    "SIGNAL": "captures predictive or edge signal contribution.",
    "SCORING": "supports future score contribution and ranking readiness.",
    "NORMALIZATION": "supports scale unit venue market and context comparability.",
    "RISK": (
        "supports future exposure drawdown loss-limit and capital-at-risk "
        "compatibility."
    ),
    "EXECUTION": (
        "supports execution-cost order-intent liquidity and slippage compatibility."
    ),
    "CAPITAL": (
        "supports sizing available-capital capital-intensity and allocation "
        "compatibility."
    ),
    "LATENCY": (
        "supports latency sensitivity timeliness and control-plane live-path "
        "separation."
    ),
    "ERROR_GUARD": (
        "supports fail-closed guardrails stale-data detection missing-input "
        "handling and invalid-state protection."
    ),
    "QUANTUM_ADVISORY": "supports future quantum optimizer advisory compatibility.",
}
ROLE_DEFINITION_REQUIRED_FIELDS = (
    "role_id",
    "role_name",
    "role_order",
    "role_required",
    "role_authority_class",
    "role_description",
    "institutional_purpose",
    "primary_purpose",
    "canonical_inputs",
    "canonical_outputs",
    "upstream_dependencies",
    "downstream_consumers",
    "missing_role_normal_state",
    "missing_role_owner_override_state",
    "owner_override_supported",
    "owner_override_satisfaction_basis_allowed",
    "single_parameter_satisfies_role",
    "single_algorithm_satisfies_role",
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_forward_compatibility",
    "deterministic_trace",
    "no_claim_flags",
)
OWNER_OVERRIDE_BASES = (
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_APPROVED",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED_OVERRIDE",
)
ROLE_FALSE_FIELDS = (
    "single_parameter_satisfies_role",
    "single_algorithm_satisfies_role",
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
)
TOP_LEVEL_FALSE_FIELDS = (
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
    "creates_stack_completeness_gate",
    "creates_stack_compatibility_gate",
    "creates_runtime_or_live_trading_authority",
    "production_stack_ready",
    "final_ready",
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
    "stack_completeness_gate_created",
    "stack_compatibility_gate_created",
    "runtime_live_use_created",
)
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
    "atomicrows_bundle_jsonl",
    "atomicrows_bundle_sha256",
    "ranking",
    "scoring",
    "optimizer_arbitration",
    "trade_context_routing",
    "stack_selection",
    "stack_completeness_gate",
    "stack_compatibility_gate",
    "runtime_live_use",
)
OWNER_OVERRIDE_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfaction_basis_supported",
    "owner_override_satisfies_internal_stack_readiness_only",
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
QUANTUM_POLICY_TRUE_FIELDS = (
    "quantum_advisory_role_required",
    "quantum_advisory_role_is_static_taxonomy_only",
    "future_quantum_applicability_registry_required_before_quantum_selection",
    "future_owner_quantum_priority_policy_required_before_quantum_priority",
    "future_scoring_ranking_gate_required_before_quantum_ranking",
    "future_quantum_classical_arbitration_gate_required_before_quantum_selection",
    "strongest_classical_comparator_required_before_quantum_advantage_claim",
    "replay_paper_evidence_required_before_advantage_claim",
    "live_evidence_required_before_profit_claim",
)
QUANTUM_POLICY_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_latency_superiority_claim_created",
    "quantum_execution_superiority_claim_created",
    "quantum_scoring_created",
    "quantum_arbitration_created",
)
FUTURE_CONSUMER_TRUE_FIELDS = (
    "pr74_completeness_gate_consumer_ready",
    "pr75_compatibility_gate_consumer_ready",
    "pr76_selection_packet_consumer_ready",
    "pr77_trade_context_consumer_ready",
    "pr78_selection_universe_consumer_ready",
    "pr81_quantum_applicability_consumer_ready",
    "pr82_owner_quantum_priority_consumer_ready",
    "pr83_scoring_policy_consumer_ready",
    "pr84_scoring_ranking_consumer_ready",
    "pr85_quantum_classical_arbitration_consumer_ready",
    "pr86_candidate_stack_generation_consumer_ready",
    "pr87_trade_context_stack_selection_consumer_ready",
    "consumer_contract_static_only",
)
FUTURE_CONSUMER_FALSE_FIELDS = (
    "runtime_consumer_created",
    "live_consumer_created",
)
FIXTURE_CASE_IDS = (
    "SYNTHETIC_VALID_ALL_ROLES_CANONICAL_ORDER",
    "SYNTHETIC_MISSING_ROLE_BLOCKS_NORMAL_READINESS",
    "SYNTHETIC_MISSING_ROLE_OWNER_OVERRIDE_INTERNAL_ONLY",
    "SYNTHETIC_SINGLE_PARAMETER_INCOMPLETE_WITHOUT_OWNER_OVERRIDE",
    "SYNTHETIC_SINGLE_PARAMETER_OWNER_OVERRIDE_INTERNAL_ONLY",
    "SYNTHETIC_SINGLE_ALGORITHM_INCOMPLETE_WITHOUT_OWNER_OVERRIDE",
    "SYNTHETIC_SINGLE_ALGORITHM_OWNER_OVERRIDE_INTERNAL_ONLY",
    "SYNTHETIC_QUANTUM_ADVISORY_STATIC_ONLY",
)
REPORT_FALSE_FIELDS = (
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
    "atomicrows_bundle_rows_created",
    "atomicrows_bundle_sha256_exists",
    "ranking_created",
    "scoring_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "stack_selection_created",
    "stack_completeness_gate_created",
    "stack_compatibility_gate_created",
    "stack_completeness_evaluated_by_this_registry",
    "stack_compatibility_evaluated_by_this_registry",
    "stack_selection_created_by_this_registry",
    "stack_scoring_created_by_this_registry",
    "optimizer_arbitration_created_by_this_registry",
    "trade_context_routing_created_by_this_registry",
    "production_stack_ready",
    "final_ready",
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_latency_superiority_claim_created",
    "quantum_execution_superiority_claim_created",
    "quantum_scoring_created",
    "quantum_arbitration_created",
)


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


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def _read_text_if_exists(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    return load_json(path)


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


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
        ("ORDER_COMMAND_SUBMIT", "submit" + " order"),
        ("ORDER_COMMAND_CANCEL", "cancel" + " order"),
        ("ORDER_COMMAND_REPLACE", "replace" + " order"),
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
        ("STACK_COMPLETE_PRODUCTION_CLAIM", "stack complete" + " as production"),
        ("STACK_COMPATIBLE_PRODUCTION_CLAIM", "stack compatible" + " as production"),
    )


def _forbidden_text_regexes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    return (
        ("SECRET_LIKE_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("ORDER_FILL_CLAIM", re.compile(r"\bfills\b", re.IGNORECASE)),
    )


def forbidden_text_findings(texts: Sequence[tuple[str, str]]) -> dict[str, bool]:
    findings = {
        "real_urls_present": False,
        "secrets_present": False,
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
        for code, pattern in _forbidden_text_regexes():
            if not pattern.search(text):
                continue
            findings["forbidden_claims_present"] = True
            if code in secret_codes:
                findings["secrets_present"] = True
    return findings


def validate_no_real_urls(payload: Any, label: str = "payload") -> list[str]:
    failures: list[str] = []
    text = json.dumps(payload, sort_keys=True) if not isinstance(payload, str) else payload
    lowered = text.lower()
    for code, pattern in _forbidden_text_patterns():
        if code in {"REAL_HTTP_LOCATOR", "REAL_HTTPS_LOCATOR", "REAL_WWW_LOCATOR"}:
            if pattern.lower() in lowered:
                failures.append(f"{code}: forbidden URL-like text appears in {label}")
    return failures


def validate_no_secret_like_values(payload: Any, label: str = "payload") -> list[str]:
    failures: list[str] = []
    text = json.dumps(payload, sort_keys=True) if not isinstance(payload, str) else payload
    lowered = text.lower()
    secret_codes = {
        "SECRET_LIKE_API_KEY",
        "SECRET_LIKE_API_KEY_UNDERSCORE",
        "SECRET_LIKE_PRIVATE_KEY",
        "SECRET_LIKE_BEARER_TOKEN",
        "SECRET_LIKE_PASSWORD",
    }
    for code, pattern in _forbidden_text_patterns():
        if code in secret_codes and pattern.lower() in lowered:
            failures.append(f"{code}: forbidden secret-like text appears in {label}")
    for code, pattern in _forbidden_text_regexes():
        if code == "SECRET_LIKE_AWS_ACCESS_KEY" and pattern.search(text):
            failures.append(f"{code}: forbidden secret-like text appears in {label}")
    return failures


def validate_no_forbidden_claims(texts: Sequence[tuple[str, str]]) -> list[str]:
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


def validate_upstream_dependencies(repo_root: pathlib.Path) -> list[str]:
    root = repo_root.resolve()
    dependency_groups = (
        (
            "PR70_CLASSIFIER_DEPENDENCY_BLOCK",
            (PR70_SCHEMA, PR70_REGISTRY, PR70_REPORT),
        ),
        (
            "PR71_INTAKE_REGISTRY_DEPENDENCY_BLOCK",
            (PR71_SCHEMA, PR71_REGISTRY, PR71_REPORT),
        ),
        (
            "PR72_CANDIDATE_FAMILY_GATE_DEPENDENCY_BLOCK",
            (PR72_SCHEMA, PR72_REGISTRY, PR72_REPORT),
        ),
    )
    failures: list[str] = []
    for code, paths in dependency_groups:
        missing = sorted(_as_posix(path) for path in paths if not (root / path).exists())
        if missing:
            failures.append(f"{code}: missing {', '.join(missing)}")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["schema.required must be a list"]
    for field in (
        "registry_id",
        "registry_version",
        "authority_class",
        "upstream_dependency_contract",
        "required_stack_roles",
        "role_definitions",
        "minimum_required_role_count",
        "role_order_policy",
        "single_parameter_set_policy",
        "single_algorithm_set_policy",
        "missing_role_policy",
        "owner_override_policy",
        "quantum_forward_role_policy",
        "future_consumer_contract",
        "forbidden_artifact_flags",
        "validation_invariants",
        "final_ready",
    ):
        if field not in required:
            failures.append(f"schema.required missing {field}")

    defs = _mapping(schema.get("$defs"))
    role_enum = _mapping(defs.get("role_id")).get("enum")
    if role_enum != list(REQUIRED_STACK_ROLES):
        failures.append("schema.$defs.role_id.enum must match canonical role order")
    role_required = _mapping(defs.get("role_definition")).get("required")
    if role_required != list(ROLE_DEFINITION_REQUIRED_FIELDS):
        failures.append("schema.$defs.role_definition.required must match contract")
    no_claim_required = _mapping(defs.get("no_claim_flags")).get("required")
    if no_claim_required != list(NO_CLAIM_FIELDS):
        failures.append("schema.$defs.no_claim_flags.required must match contract")
    forbidden_required = _mapping(defs.get("forbidden_artifact_flags")).get("required")
    if forbidden_required != list(FORBIDDEN_ARTIFACT_FLAG_FIELDS):
        failures.append("schema.$defs.forbidden_artifact_flags.required must match contract")
    return failures


def _expect_bool(
    payload: dict[str, Any],
    field: str,
    expected: bool,
    label: str,
) -> list[str]:
    if payload.get(field) is expected:
        return []
    return [f"{label}.{field} must be {expected!r}"]


def validate_required_roles(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    roles = registry.get("required_stack_roles")
    if roles != list(REQUIRED_STACK_ROLES):
        failures.append("required_stack_roles must match canonical PR73 role order")
    if registry.get("minimum_required_role_count") != len(REQUIRED_STACK_ROLES):
        failures.append("minimum_required_role_count must be 9")
    return failures


def validate_role_definitions(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    definitions = _list_of_mappings(registry.get("role_definitions"))
    if len(definitions) != len(REQUIRED_STACK_ROLES):
        failures.append("role_definitions must contain exactly nine records")
    role_ids = [definition.get("role_id") for definition in definitions]
    if role_ids != list(REQUIRED_STACK_ROLES):
        failures.append("role_definitions role_id order must match required_stack_roles")
    if len(role_ids) != len(set(role_ids)):
        failures.append("role_definitions role_id values must be unique")

    for expected_order, role_id in enumerate(REQUIRED_STACK_ROLES, start=1):
        matches = [
            definition for definition in definitions if definition.get("role_id") == role_id
        ]
        if len(matches) != 1:
            failures.append(f"role_definitions must include exactly one {role_id}")
            continue
        role = matches[0]
        label = f"role_definitions.{role_id}"
        if set(role) != set(ROLE_DEFINITION_REQUIRED_FIELDS):
            unexpected = sorted(set(role) - set(ROLE_DEFINITION_REQUIRED_FIELDS))
            missing = sorted(set(ROLE_DEFINITION_REQUIRED_FIELDS) - set(role))
            failures.append(
                f"{label} fields mismatch missing={missing} unexpected={unexpected}"
            )
        if role.get("role_order") != expected_order:
            failures.append(f"{label}.role_order must be {expected_order}")
        if role.get("role_required") is not True:
            failures.append(f"{label}.role_required must be true")
        if role.get("institutional_purpose") != ROLE_INSTITUTIONAL_PURPOSES[role_id]:
            failures.append(f"{label}.institutional_purpose must match canonical text")
        if role.get("missing_role_normal_state") != "BLOCKS_NORMAL_STACK_READINESS":
            failures.append(f"{label}.missing_role_normal_state must block readiness")
        if role.get("missing_role_owner_override_state") != OWNER_OVERRIDE_INTERNAL_ONLY:
            failures.append(f"{label}.missing_role_owner_override_state mismatch")
        if role.get("owner_override_supported") is not True:
            failures.append(f"{label}.owner_override_supported must be true")
        if role.get("owner_override_satisfaction_basis_allowed") != list(OWNER_OVERRIDE_BASES):
            failures.append(f"{label}.owner_override_satisfaction_basis_allowed mismatch")
        for field in ROLE_FALSE_FIELDS:
            failures.extend(_expect_bool(role, field, False, label))

        trace = _mapping(role.get("deterministic_trace"))
        trace_expected = {
            "role_id": role_id,
            "role_order": expected_order,
            "deterministic_role_id": (
                f"ATOMICROWS_PARAMETER_STACK_ROLE_{expected_order:03d}_{role_id}"
            ),
            "random_selection_used": False,
            "ranking_used": False,
            "scoring_used": False,
            "optimizer_arbitration_used": False,
            "trade_context_routing_used": False,
            "stack_selection_used": False,
        }
        for field, expected in trace_expected.items():
            if trace.get(field) != expected:
                failures.append(f"{label}.deterministic_trace.{field} mismatch")

        no_claims = _mapping(role.get("no_claim_flags"))
        if set(no_claims) != set(NO_CLAIM_FIELDS):
            failures.append(f"{label}.no_claim_flags fields must match contract")
        for field in NO_CLAIM_FIELDS:
            failures.extend(_expect_bool(no_claims, field, False, f"{label}.no_claim_flags"))

        quantum = _mapping(role.get("quantum_forward_compatibility"))
        for field in (
            "strongest_classical_comparator_required",
            "fallback_bundle_required",
            "replay_paper_evidence_required_before_advantage_claim",
            "live_evidence_required_before_profit_claim",
        ):
            failures.extend(_expect_bool(quantum, field, True, f"{label}.quantum_forward_compatibility"))
        for field in (
            "quantum_backend_execution_created",
            "quantum_advantage_claim_created",
        ):
            failures.extend(_expect_bool(quantum, field, False, f"{label}.quantum_forward_compatibility"))

    quantum_role = next(
        (
            definition
            for definition in definitions
            if definition.get("role_id") == "QUANTUM_ADVISORY"
        ),
        {},
    )
    quantum_compatibility = _mapping(quantum_role.get("quantum_forward_compatibility"))
    quantum_true_fields = (
        "true_quantum_review_compatible",
        "quantum_inspired_review_compatible",
        "hybrid_classical_quantum_review_compatible",
        "qubo_compatible_review",
        "ising_compatible_review",
        "qaoa_compatible_review",
        "vqe_compatible_review",
        "annealing_compatible_review",
        "quantum_portfolio_optimization_review",
        "owner_quantum_priority_compatible",
        "owner_forced_quantum_compatible",
        "hybrid_compare_then_quantum_tiebreak_compatible",
    )
    for field in quantum_true_fields:
        failures.extend(
            _expect_bool(
                quantum_compatibility,
                field,
                True,
                "role_definitions.QUANTUM_ADVISORY.quantum_forward_compatibility",
            )
        )
    return failures


def validate_role_order_policy(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("role_order_policy"))
    failures: list[str] = []
    for field in (
        "required_stack_roles_order_is_canonical",
        "role_order_must_be_stable",
        "role_order_must_not_be_random",
    ):
        failures.extend(_expect_bool(policy, field, True, "role_order_policy"))
    return failures


def validate_single_parameter_policy(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("single_parameter_set_policy"))
    failures: list[str] = []
    expected = {
        "single_parameter_set_complete_without_owner_override": False,
        "single_parameter_set_complete_with_owner_override": True,
        "owner_override_state": OWNER_OVERRIDE_INTERNAL_ONLY,
        "external_fact_fabrication_allowed": False,
        "accepted_source_packet_fabrication_allowed": False,
        "runtime_use_created": False,
        "live_use_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            failures.append(f"single_parameter_set_policy.{field} must be {value!r}")
    return failures


def validate_single_algorithm_policy(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("single_algorithm_set_policy"))
    failures: list[str] = []
    expected = {
        "single_algorithm_set_complete_without_owner_override": False,
        "single_algorithm_set_complete_with_owner_override": True,
        "owner_override_state": OWNER_OVERRIDE_INTERNAL_ONLY,
        "external_fact_fabrication_allowed": False,
        "accepted_source_packet_fabrication_allowed": False,
        "runtime_use_created": False,
        "live_use_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            failures.append(f"single_algorithm_set_policy.{field} must be {value!r}")
    return failures


def validate_missing_role_policy(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("missing_role_policy"))
    failures: list[str] = []
    expected = {
        "missing_required_role_blocks_normal_stack_readiness": True,
        "missing_required_role_owner_override_state": OWNER_OVERRIDE_INTERNAL_ONLY,
        "missing_required_role_creates_final_ready": False,
        "missing_required_role_creates_runtime_use": False,
        "missing_required_role_creates_live_use": False,
        "missing_required_role_creates_order_authority": False,
        "missing_required_role_creates_profit_evidence": False,
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            failures.append(f"missing_role_policy.{field} must be {value!r}")
    return failures


def validate_owner_override_policy(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("owner_override_policy"))
    failures: list[str] = []
    for field in OWNER_OVERRIDE_TRUE_FIELDS:
        failures.extend(_expect_bool(policy, field, True, "owner_override_policy"))
    for field in OWNER_OVERRIDE_FALSE_FIELDS:
        failures.extend(_expect_bool(policy, field, False, "owner_override_policy"))
    return failures


def validate_quantum_advisory_boundary(registry: dict[str, Any]) -> list[str]:
    policy = _mapping(registry.get("quantum_forward_role_policy"))
    failures: list[str] = []
    for field in QUANTUM_POLICY_TRUE_FIELDS:
        failures.extend(_expect_bool(policy, field, True, "quantum_forward_role_policy"))
    for field in QUANTUM_POLICY_FALSE_FIELDS:
        failures.extend(_expect_bool(policy, field, False, "quantum_forward_role_policy"))
    role_ids = [
        role.get("role_id")
        for role in _list_of_mappings(registry.get("role_definitions"))
    ]
    if "QUANTUM_ADVISORY" not in role_ids:
        failures.append("QUANTUM_ADVISORY role must exist")
    return failures


def validate_future_consumer_contract(registry: dict[str, Any]) -> list[str]:
    contract = _mapping(registry.get("future_consumer_contract"))
    failures: list[str] = []
    for field in FUTURE_CONSUMER_TRUE_FIELDS:
        failures.extend(_expect_bool(contract, field, True, "future_consumer_contract"))
    for field in FUTURE_CONSUMER_FALSE_FIELDS:
        failures.extend(_expect_bool(contract, field, False, "future_consumer_contract"))
    return failures


def validate_no_forbidden_artifacts(repo_root: pathlib.Path) -> list[str]:
    root = repo_root.resolve()
    failures: list[str] = []
    if (root / CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            f"ATOMICROWS_BUNDLE_SHA_FORBIDDEN_ARTIFACT_BLOCK: {_as_posix(CANONICAL_BUNDLE_SHA256)}"
        )
    return failures


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--", _as_posix(MASTER_PLAN_CURRENT)],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [
            "MASTER_PLAN_EDIT_GUARD_UNAVAILABLE: git diff failed: "
            + completed.stderr.strip()
        ]
    if completed.stdout.strip():
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR73"]
    return []


def _validate_forbidden_flags(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden = _mapping(registry.get("forbidden_artifact_flags"))
    if set(forbidden) != set(FORBIDDEN_ARTIFACT_FLAG_FIELDS):
        failures.append("forbidden_artifact_flags fields must match PR73 contract")
    for field in FORBIDDEN_ARTIFACT_FLAG_FIELDS:
        failures.extend(_expect_bool(forbidden, field, False, "forbidden_artifact_flags"))
    for field in TOP_LEVEL_FALSE_FIELDS:
        failures.extend(_expect_bool(registry, field, False, "production_registry"))
    return failures


def _validate_upstream_contract(registry: dict[str, Any]) -> list[str]:
    contract = _mapping(registry.get("upstream_dependency_contract"))
    expected = {
        "pr70_classifier_dependency_preserved": True,
        "pr71_intake_registry_dependency_preserved": True,
        "pr72_candidate_family_gate_dependency_preserved": True,
        "upstream_semantics_mutated_by_this_registry": False,
    }
    failures: list[str] = []
    for field, value in expected.items():
        if contract.get(field) != value:
            failures.append(f"upstream_dependency_contract.{field} must be {value!r}")
    return failures


def validate_registry_payload(
    registry: dict[str, Any],
    *,
    schema: dict[str, Any],
    label: str = "production_registry",
) -> list[str]:
    failures: list[str] = []
    failures.extend(validate_json_schema_subset(registry, schema))
    expected_top = {
        "registry_id": REGISTRY_ID,
        "registry_version": REGISTRY_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "role_taxonomy_contract_ready": True,
        "stack_completeness_evaluated_by_this_registry": False,
        "stack_compatibility_evaluated_by_this_registry": False,
        "stack_selection_created_by_this_registry": False,
        "stack_scoring_created_by_this_registry": False,
        "optimizer_arbitration_created_by_this_registry": False,
        "trade_context_routing_created_by_this_registry": False,
        "production_stack_ready": False,
        "final_ready": False,
    }
    for field, expected in expected_top.items():
        if registry.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")
    failures.extend(_validate_upstream_contract(registry))
    failures.extend(validate_required_roles(registry))
    failures.extend(validate_role_definitions(registry))
    failures.extend(validate_role_order_policy(registry))
    failures.extend(validate_single_parameter_policy(registry))
    failures.extend(validate_single_algorithm_policy(registry))
    failures.extend(validate_missing_role_policy(registry))
    failures.extend(validate_owner_override_policy(registry))
    failures.extend(validate_quantum_advisory_boundary(registry))
    failures.extend(validate_future_consumer_contract(registry))
    failures.extend(_validate_forbidden_flags(registry))
    if not isinstance(registry.get("validation_invariants"), list):
        failures.append(f"{label}.validation_invariants must be a list")
    text = json.dumps(registry, sort_keys=True)
    failures.extend(validate_no_real_urls(text, label))
    failures.extend(validate_no_secret_like_values(text, label))
    failures.extend(validate_no_forbidden_claims(((label, text),)))
    return failures


def _fixture_cases(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(fixture.get("fixture_cases"))


def validate_fixture_payload(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_root = {
        "fixture_id": "SYNTHETIC_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_FIXTURE",
        "fixture_version": (
            "SYNTHETIC_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_FIXTURE_V1"
        ),
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
    }
    for field, expected in expected_root.items():
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected!r}")
    cases = _fixture_cases(fixture)
    case_ids = [case.get("case_id") for case in cases]
    if case_ids != list(FIXTURE_CASE_IDS):
        failures.append("fixture.fixture_cases must use canonical PR73 case order")
    for case in cases:
        label = f"fixture.{case.get('case_id')}"
        if case.get("synthetic_case_only") is not True:
            failures.append(f"{label}.synthetic_case_only must be true")
        role_ids = case.get("role_ids")
        if role_ids is not None:
            if not isinstance(role_ids, list):
                failures.append(f"{label}.role_ids must be a list")
            elif any(role_id not in REQUIRED_STACK_ROLES for role_id in role_ids):
                failures.append(f"{label}.role_ids contains unknown role")
        expected_state = _mapping(case.get("expected_state"))
        if expected_state.get("runtime_use_created") is True:
            failures.append(f"{label}.expected_state.runtime_use_created must be false")
        if expected_state.get("evidence_fabricated") is True:
            failures.append(f"{label}.expected_state.evidence_fabricated must be false")

    case_by_id = {case.get("case_id"): case for case in cases}
    valid_case = _mapping(case_by_id.get("SYNTHETIC_VALID_ALL_ROLES_CANONICAL_ORDER"))
    if valid_case.get("role_ids") != list(REQUIRED_STACK_ROLES):
        failures.append("valid fixture case must contain all roles in canonical order")
    missing_case = _mapping(case_by_id.get("SYNTHETIC_MISSING_ROLE_BLOCKS_NORMAL_READINESS"))
    missing_state = _mapping(missing_case.get("expected_state"))
    if missing_state.get("normal_stack_readiness_blocked") is not True:
        failures.append("missing-role fixture case must block normal readiness")
    override_case = _mapping(case_by_id.get("SYNTHETIC_MISSING_ROLE_OWNER_OVERRIDE_INTERNAL_ONLY"))
    override_state = _mapping(override_case.get("expected_state"))
    if override_case.get("owner_override_basis") != "OWNER_GLOBAL_OVERRIDE":
        failures.append("owner override fixture case must use OWNER_GLOBAL_OVERRIDE")
    if override_state.get("owner_override_state") != OWNER_OVERRIDE_INTERNAL_ONLY:
        failures.append("owner override fixture case must map to internal-only state")

    single_parameter = _mapping(
        case_by_id.get("SYNTHETIC_SINGLE_PARAMETER_INCOMPLETE_WITHOUT_OWNER_OVERRIDE")
    )
    if _mapping(single_parameter.get("expected_state")).get("single_parameter_set_complete") is not False:
        failures.append("single parameter fixture case must be incomplete without override")
    single_parameter_override = _mapping(
        case_by_id.get("SYNTHETIC_SINGLE_PARAMETER_OWNER_OVERRIDE_INTERNAL_ONLY")
    )
    if _mapping(single_parameter_override.get("expected_state")).get("single_parameter_set_complete") is not True:
        failures.append("single parameter owner override fixture case must be internally satisfied")

    single_algorithm = _mapping(
        case_by_id.get("SYNTHETIC_SINGLE_ALGORITHM_INCOMPLETE_WITHOUT_OWNER_OVERRIDE")
    )
    if _mapping(single_algorithm.get("expected_state")).get("single_algorithm_set_complete") is not False:
        failures.append("single algorithm fixture case must be incomplete without override")
    single_algorithm_override = _mapping(
        case_by_id.get("SYNTHETIC_SINGLE_ALGORITHM_OWNER_OVERRIDE_INTERNAL_ONLY")
    )
    if _mapping(single_algorithm_override.get("expected_state")).get("single_algorithm_set_complete") is not True:
        failures.append("single algorithm owner override fixture case must be internally satisfied")

    quantum_case = _mapping(case_by_id.get("SYNTHETIC_QUANTUM_ADVISORY_STATIC_ONLY"))
    quantum_state = _mapping(quantum_case.get("expected_state"))
    for field, expected in {
        "quantum_advisory_role_required": True,
        "quantum_advisory_role_is_static_taxonomy_only": True,
        "quantum_backend_execution_created": False,
        "quantum_scoring_created": False,
        "quantum_arbitration_created": False,
    }.items():
        if quantum_state.get(field) != expected:
            failures.append(f"quantum fixture case {field} must be {expected!r}")

    text = json.dumps(fixture, sort_keys=True)
    failures.extend(validate_no_real_urls(text, "fixture"))
    failures.extend(validate_no_secret_like_values(text, "fixture"))
    failures.extend(validate_no_forbidden_claims((("fixture", text),)))
    return failures


def fixture_contains_only_synthetic_cases(fixture: dict[str, Any]) -> bool:
    return (
        fixture.get("fixture_id")
        == "SYNTHETIC_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_FIXTURE"
        and all(case.get("synthetic_case_only") is True for case in _fixture_cases(fixture))
    )


def _flag(registry: dict[str, Any], field: str) -> bool:
    return bool(registry.get(field))


def _forbidden_flag(registry: dict[str, Any], field: str) -> bool:
    return bool(_mapping(registry.get("forbidden_artifact_flags")).get(field))


def _owner_override_flag(registry: dict[str, Any], field: str) -> bool:
    return bool(_mapping(registry.get("owner_override_policy")).get(field))


def _quantum_flag(registry: dict[str, Any], field: str) -> bool:
    return bool(_mapping(registry.get("quantum_forward_role_policy")).get(field))


def build_report(
    *,
    repo_root: pathlib.Path,
    registry: dict[str, Any],
    fixture: dict[str, Any],
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    root = repo_root.resolve()
    role_ids = [
        role.get("role_id")
        for role in _list_of_mappings(registry.get("role_definitions"))
    ]
    return {
        "accepted_source_packets_created": _flag(
            registry, "creates_accepted_source_packets"
        ),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_rows_created": _flag(
            registry, "creates_atomicrows_bundle_rows"
        ),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "capital_role_present": "CAPITAL" in role_ids,
        "cash_receipts_created": _flag(registry, "creates_cash_receipts"),
        "connector_semantics_created": _flag(registry, "creates_connector_semantics"),
        "depends_on_pr70_classifier": True,
        "depends_on_pr71_intake_registry": True,
        "depends_on_pr72_candidate_family_gate": True,
        "error_guard_role_present": "ERROR_GUARD" in role_ids,
        "execution_role_present": "EXECUTION" in role_ids,
        "execution_superiority_claim_created": _flag(
            registry, "creates_execution_superiority_claim"
        ),
        "final_ready": registry.get("final_ready"),
        "fixture_contains_only_synthetic_cases": fixture_contains_only_synthetic_cases(
            fixture
        ),
        "fixture_path": _as_posix(fixture_path),
        "future_owner_quantum_priority_policy_required_before_quantum_priority": (
            _quantum_flag(
                registry,
                "future_owner_quantum_priority_policy_required_before_quantum_priority",
            )
        ),
        "future_quantum_applicability_registry_required_before_quantum_selection": (
            _quantum_flag(
                registry,
                "future_quantum_applicability_registry_required_before_quantum_selection",
            )
        ),
        "future_quantum_classical_arbitration_gate_required_before_quantum_selection": (
            _quantum_flag(
                registry,
                "future_quantum_classical_arbitration_gate_required_before_quantum_selection",
            )
        ),
        "future_scoring_ranking_gate_required_before_quantum_ranking": _quantum_flag(
            registry, "future_scoring_ranking_gate_required_before_quantum_ranking"
        ),
        "latency_role_present": "LATENCY" in role_ids,
        "latency_superiority_claim_created": _flag(
            registry, "creates_latency_superiority_claim"
        ),
        "live_evidence_required_before_profit_claim": _quantum_flag(
            registry, "live_evidence_required_before_profit_claim"
        ),
        "live_readiness_created": _flag(registry, "creates_live_readiness"),
        "live_receipts_created": _forbidden_flag(registry, "live_receipts"),
        "minimum_required_role_count": registry.get("minimum_required_role_count"),
        "missing_required_role_blocks_normal_stack_readiness": _mapping(
            registry.get("missing_role_policy")
        ).get("missing_required_role_blocks_normal_stack_readiness"),
        "missing_required_role_owner_override_state": _mapping(
            registry.get("missing_role_policy")
        ).get("missing_required_role_owner_override_state"),
        "normalization_role_present": "NORMALIZATION" in role_ids,
        "optimizer_arbitration_created": _flag(
            registry, "creates_optimizer_arbitration"
        ),
        "optimizer_arbitration_created_by_this_registry": registry.get(
            "optimizer_arbitration_created_by_this_registry"
        ),
        "order_authority_created": _flag(registry, "creates_order_authority"),
        "order_receipts_created": _forbidden_flag(registry, "order_receipts"),
        "owner_override_fabricates_accepted_source_packet": _owner_override_flag(
            registry, "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_connector_semantic": _owner_override_flag(
            registry, "owner_override_fabricates_connector_semantic"
        ),
        "owner_override_fabricates_external_fact": _owner_override_flag(
            registry, "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": _owner_override_flag(
            registry, "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": _owner_override_flag(
            registry, "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": _owner_override_flag(
            registry, "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": _owner_override_flag(
            registry, "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": _owner_override_flag(
            registry, "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_satisfies_internal_stack_readiness_only": _owner_override_flag(
            registry, "owner_override_satisfies_internal_stack_readiness_only"
        ),
        "owner_override_supported": _owner_override_flag(
            registry, "owner_override_supported"
        ),
        "paper_results_created": _flag(registry, "creates_paper_results"),
        "production_stack_ready": registry.get("production_stack_ready"),
        "profit_evidence_created": _flag(registry, "creates_profit_evidence"),
        "quantum_advantage_claim_created": _quantum_flag(
            registry, "quantum_advantage_claim_created"
        ),
        "quantum_advisory_role_is_static_taxonomy_only": _quantum_flag(
            registry, "quantum_advisory_role_is_static_taxonomy_only"
        ),
        "quantum_advisory_role_present": "QUANTUM_ADVISORY" in role_ids,
        "quantum_advisory_role_required": _quantum_flag(
            registry, "quantum_advisory_role_required"
        ),
        "quantum_arbitration_created": _quantum_flag(
            registry, "quantum_arbitration_created"
        ),
        "quantum_backend_evidence_created": _flag(
            registry, "creates_quantum_backend_evidence"
        ),
        "quantum_backend_execution_created": _quantum_flag(
            registry, "quantum_backend_execution_created"
        ),
        "quantum_execution_superiority_claim_created": _quantum_flag(
            registry, "quantum_execution_superiority_claim_created"
        ),
        "quantum_latency_superiority_claim_created": _quantum_flag(
            registry, "quantum_latency_superiority_claim_created"
        ),
        "quantum_scoring_created": _quantum_flag(registry, "quantum_scoring_created"),
        "ranking_created": _flag(registry, "creates_ranking"),
        "replay_paper_evidence_required_before_advantage_claim": _quantum_flag(
            registry, "replay_paper_evidence_required_before_advantage_claim"
        ),
        "replay_results_created": _flag(registry, "creates_replay_results"),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_stack_role_count": len(registry.get("required_stack_roles", [])),
        "required_stack_roles_order_valid": registry.get("required_stack_roles")
        == list(REQUIRED_STACK_ROLES),
        "required_stack_roles_present": set(registry.get("required_stack_roles", []))
        == set(REQUIRED_STACK_ROLES),
        "risk_role_present": "RISK" in role_ids,
        "role_definition_count": len(role_ids),
        "role_definitions_complete": role_ids == list(REQUIRED_STACK_ROLES),
        "role_taxonomy_contract_ready": registry.get("role_taxonomy_contract_ready"),
        "runtime_artifacts_created": _flag(registry, "creates_runtime_artifacts"),
        "runtime_receipts_created": _forbidden_flag(registry, "runtime_receipts"),
        "scoring_created": _flag(registry, "creates_scoring"),
        "scoring_role_present": "SCORING" in role_ids,
        "signal_role_present": "SIGNAL" in role_ids,
        "single_algorithm_set_complete_with_owner_override": _mapping(
            registry.get("single_algorithm_set_policy")
        ).get("single_algorithm_set_complete_with_owner_override"),
        "single_algorithm_set_complete_without_owner_override": _mapping(
            registry.get("single_algorithm_set_policy")
        ).get("single_algorithm_set_complete_without_owner_override"),
        "single_parameter_set_complete_with_owner_override": _mapping(
            registry.get("single_parameter_set_policy")
        ).get("single_parameter_set_complete_with_owner_override"),
        "single_parameter_set_complete_without_owner_override": _mapping(
            registry.get("single_parameter_set_policy")
        ).get("single_parameter_set_complete_without_owner_override"),
        "source_acceptance_created": _flag(registry, "accepts_source_facts"),
        "source_retrieval_created": _flag(registry, "retrieves_source_facts"),
        "stack_compatibility_evaluated_by_this_registry": registry.get(
            "stack_compatibility_evaluated_by_this_registry"
        ),
        "stack_compatibility_gate_created": _flag(
            registry, "creates_stack_compatibility_gate"
        ),
        "stack_completeness_evaluated_by_this_registry": registry.get(
            "stack_completeness_evaluated_by_this_registry"
        ),
        "stack_completeness_gate_created": _flag(
            registry, "creates_stack_completeness_gate"
        ),
        "stack_scoring_created_by_this_registry": registry.get(
            "stack_scoring_created_by_this_registry"
        ),
        "stack_selection_created": _flag(registry, "creates_stack_selection"),
        "stack_selection_created_by_this_registry": registry.get(
            "stack_selection_created_by_this_registry"
        ),
        "strongest_classical_comparator_required_before_quantum_advantage_claim": (
            _quantum_flag(
                registry,
                "strongest_classical_comparator_required_before_quantum_advantage_claim",
            )
        ),
        "trade_context_routing_created": _flag(
            registry, "creates_trade_context_routing"
        ),
        "trade_context_routing_created_by_this_registry": registry.get(
            "trade_context_routing_created_by_this_registry"
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
        "depends_on_pr70_classifier": True,
        "depends_on_pr71_intake_registry": True,
        "depends_on_pr72_candidate_family_gate": True,
        "required_stack_role_count": len(REQUIRED_STACK_ROLES),
        "required_stack_roles_present": True,
        "required_stack_roles_order_valid": True,
        "role_definition_count": len(REQUIRED_STACK_ROLES),
        "role_definitions_complete": True,
        "minimum_required_role_count": len(REQUIRED_STACK_ROLES),
        "signal_role_present": True,
        "scoring_role_present": True,
        "normalization_role_present": True,
        "risk_role_present": True,
        "execution_role_present": True,
        "capital_role_present": True,
        "latency_role_present": True,
        "error_guard_role_present": True,
        "quantum_advisory_role_present": True,
        "single_parameter_set_complete_without_owner_override": False,
        "single_algorithm_set_complete_without_owner_override": False,
        "single_parameter_set_complete_with_owner_override": True,
        "single_algorithm_set_complete_with_owner_override": True,
        "missing_required_role_blocks_normal_stack_readiness": True,
        "missing_required_role_owner_override_state": OWNER_OVERRIDE_INTERNAL_ONLY,
        "role_taxonomy_contract_ready": True,
        "owner_override_supported": True,
        "owner_override_satisfies_internal_stack_readiness_only": True,
        "quantum_advisory_role_required": True,
        "quantum_advisory_role_is_static_taxonomy_only": True,
        "future_quantum_applicability_registry_required_before_quantum_selection": True,
        "future_owner_quantum_priority_policy_required_before_quantum_priority": True,
        "future_scoring_ranking_gate_required_before_quantum_ranking": True,
        "future_quantum_classical_arbitration_gate_required_before_quantum_selection": True,
        "strongest_classical_comparator_required_before_quantum_advantage_claim": True,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
        "fixture_contains_only_synthetic_cases": True,
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
        failures.append("report output is not deterministic JSON")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    failures.extend(validate_upstream_dependencies(root))

    schema, schema_failures = _load_json_checked(root / schema_path, "PR73_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        registry = load_yaml(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    try:
        fixture = load_fixture(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    if schema:
        failures.extend(validate_registry_payload(registry, schema=schema))
    failures.extend(validate_fixture_payload(fixture))

    artifact_texts = (
        (_as_posix(schema_path), _read_text_if_exists(root / schema_path)),
        (_as_posix(registry_path), _read_text_if_exists(root / registry_path)),
        (_as_posix(fixture_path), _read_text_if_exists(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        repo_root=root,
        registry=registry,
        fixture=fixture,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        repo_root=root,
        registry=registry,
        fixture=fixture,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR73 report is not deterministic")
    report_text = serialize_report(report)
    failures.extend(validate_no_forbidden_claims((("generated_report", report_text),)))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: parameter-stack role taxonomy is static "
            "taxonomy metadata only"
        )

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dev", choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
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
