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

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
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
    / "atomicrows_parameter_agent_binding_registry.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomic_rows"
    / "AtomicRowsParameterAgentBindingRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_agent_binding_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterAgentBindingReport.json"
)

CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REPORT_TYPE = "ATOMICROWS_PARAMETER_AGENT_BINDING_REPORT"
REGISTRY_NAME = "AtomicRowsParameterAgentBindingRegistry"
REGISTRY_MODEL = "PARAMETER_AGENT_BINDING_REGISTRY"
AUTHORITY_CLASS = (
    "STATIC_PARAMETER_AGENT_BINDING_REGISTRY_ONLY_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
)
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_FINAL_INCOMPLETE"
)
VALIDATION_HOOK = "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_STATIC_VALIDATION"

BINDING_STATUSES = (
    "ACTIVE_BINDING",
    "OWNER_APPROVED_BINDING",
    "OWNER_GLOBAL_OVERRIDE_BINDING",
    "RESEARCH_ONLY_BINDING",
    "REPLAY_PAPER_BINDING",
    "OPTIMIZER_BINDING",
    "RUNTIME_BINDING",
    "LIVE_BINDING",
    "QUANTUM_BACKEND_BINDING",
    "QUARANTINED_BINDING",
    "RETIRED_BINDING",
    "BLOCKED_PENDING_OWNER_APPROVAL",
    "BLOCKED_PENDING_AGENT_ASSIGNMENT",
    "BLOCKED_PENDING_LIFECYCLE_STATUS",
    "BLOCKED_PENDING_RECEIPTS",
)

AGENT_ROLES = (
    "OWNER",
    "ORCHESTRATOR_AGENT",
    "MASTER_PLAN_AGENT",
    "ATOMICROWS_AGENT",
    "ATOMICROWS_RESEARCH_AGENT",
    "ATOMICROWS_LIFECYCLE_AGENT",
    "SOURCE_EVIDENCE_AGENT",
    "CONNECTOR_AGENT",
    "RUNTIME_RESOLVER_AGENT",
    "REPLAY_AGENT",
    "PAPER_AGENT",
    "DUAL_RESULT_REVIEW_AGENT",
    "OPTIMIZER_AGENT",
    "RISK_AGENT",
    "SIZING_AGENT",
    "EXECUTION_LATENCY_AGENT",
    "ORDER_ROUTER_AGENT",
    "LIVE_CANARY_AGENT",
    "QUANTUM_RESEARCH_AGENT",
    "QUANTUM_BACKEND_AGENT",
    "DASHBOARD_AGENT",
    "GOVERNANCE_AGENT",
    "VALIDATION_AGENT",
    "COMPLIANCE_MARKER_AGENT",
    "OWNER_APPROVAL_REQUEST_AGENT",
)

CONSUMER_CLASSES = (
    "INVENTORY_INDEX",
    "RESEARCH_TRIAGE",
    "SOURCE_EVIDENCE_RETRIEVAL",
    "RANGE_VALIDATION",
    "REPLAY_CANDIDATE_SELECTION",
    "PAPER_CANDIDATE_SELECTION",
    "OPTIMIZER_SEARCH",
    "OPTIMIZER_DEFAULTS",
    "RISK_MODEL_INPUT",
    "SIZING_MODEL_INPUT",
    "QUANTUM_CIRCUIT_CONSTRUCTION",
    "QUANTUM_BACKEND_EXECUTION",
    "RUNTIME_RESOLVER_INPUT",
    "LIVE_ORDER_ROUTING",
    "LIVE_EXECUTION",
)

AGENT_USE_SCOPES = (
    "INVENTORY_ONLY",
    "RESEARCH_ONLY",
    "SOURCE_EVIDENCE_ONLY",
    "RANGE_VALIDATION_ONLY",
    "REPLAY_ONLY",
    "PAPER_ONLY",
    "REPLAY_PAPER_ONLY",
    "OPTIMIZER_ONLY",
    "RISK_ONLY",
    "SIZING_ONLY",
    "RUNTIME_ONLY",
    "LIVE_ONLY",
    "QUANTUM_RESEARCH_ONLY",
    "QUANTUM_BACKEND_ONLY",
    "OWNER_APPROVED_SCOPE",
    "OWNER_GLOBAL_OVERRIDE_SCOPE",
    "QUARANTINE_REVIEW_ONLY",
    "RETIREMENT_AUDIT_ONLY",
)

OWNER_OVERRIDE_TOKENS = (
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

OWNER_OVERRIDE_FINAL_STATUSES = {
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED",
    "OWNER_GLOBAL_OVERRIDE",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
}

FINAL_QTT_INTERNAL_STATUSES = (
    *BINDING_STATUSES,
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED",
    "OWNER_GLOBAL_OVERRIDE",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
)

BINDING_FIELDS = (
    "binding_id",
    "binding_status",
    "binding_authority_basis",
    "owner_override_allowed",
    "owner_override_applied",
    "owner_override_satisfaction_basis",
    "owner_approved_value",
    "parameter_family",
    "atomic_parameter_row_id",
    "row_pattern_id",
    "owning_agent_role",
    "authorized_agent_roles",
    "blocked_agent_roles",
    "authorized_agent_ids",
    "blocked_agent_ids",
    "authorized_consumer_classes",
    "blocked_consumer_classes",
    "agent_use_scope",
    "requires_lifecycle_status_at_least",
    "requires_receipts",
    "requires_owner_override_when_missing",
    "runtime_use_allowed",
    "live_use_allowed",
    "optimizer_use_allowed",
    "quantum_backend_use_allowed",
    "replay_paper_use_allowed",
    "research_use_allowed",
    "source_evidence_use_allowed",
    "binding_notes",
    "final_qtt_internal_status",
    "blocks_qtt_when_owner_override_present",
)

ROOT_FIELDS = (
    "schema_version",
    "registry_name",
    "registry_model",
    "authority_class",
    "source_master_plan",
    "canonical_source_for_parameter_agent_assignment",
    "final_expected_row_coverage",
    "deterministic_output",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "validator_authority_over_owner",
    "generated_report_authority_over_owner",
    "static_gate_authority_over_owner",
    "uses_pr_number_as_authority",
    "binding_statuses",
    "agent_roles",
    "consumer_classes",
    "agent_use_scopes",
    "lifecycle_statuses",
    "owner_override_tokens",
    "authority_boundary",
    "bindings",
)

FIXTURE_FIELDS = (
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "validation_hook_ids",
    "assignment_checks",
)

AUTHORITY_BOUNDARY_FIELDS = (
    "real_runtime_artifact_created",
    "real_live_artifact_created",
    "real_order_artifact_created",
    "real_quantum_backend_artifact_created",
    "real_profit_artifact_created",
    "creates_source_acceptance",
    "creates_connector_binding",
    "creates_runtime_receipts",
    "creates_live_receipts",
    "creates_order_receipts",
    "creates_cash_receipts",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_sha",
    "creates_sha_freeze_authority",
    "creates_dashboard_runtime_ui",
    "creates_live_trading_execution",
    "fetches_private_account_state",
    "materializes_secrets",
    "clones_external_repos",
    "installs_packages",
    "reduces_blockers",
    "validator_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "chatgpt_authority_over_owner",
    "generated_report_authority_over_owner",
    "static_gate_authority_over_owner",
)

QUARANTINE_REVIEW_ROLES = {
    "GOVERNANCE_AGENT",
    "VALIDATION_AGENT",
}

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AssignmentDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _bool(value: Any) -> bool:
    return value is True


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _present_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _normalize_path(path: pathlib.Path | str | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def _normalize_authority_boundary(value: Any) -> dict[str, bool]:
    item = _mapping(value)
    return {field: _bool(item.get(field)) for field in AUTHORITY_BOUNDARY_FIELDS}


def _normalize_binding(binding: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: binding.get(field) for field in BINDING_FIELDS}
    for field in (
        "binding_id",
        "binding_status",
        "binding_authority_basis",
        "owner_override_satisfaction_basis",
        "owner_approved_value",
        "parameter_family",
        "atomic_parameter_row_id",
        "row_pattern_id",
        "owning_agent_role",
        "agent_use_scope",
        "requires_lifecycle_status_at_least",
        "binding_notes",
        "final_qtt_internal_status",
    ):
        normalized[field] = _string_or_none(normalized.get(field))
    for field in (
        "authorized_agent_roles",
        "blocked_agent_roles",
        "authorized_agent_ids",
        "blocked_agent_ids",
        "authorized_consumer_classes",
        "blocked_consumer_classes",
        "requires_receipts",
    ):
        normalized[field] = _string_list(normalized.get(field))
    for field in (
        "owner_override_allowed",
        "owner_override_applied",
        "requires_owner_override_when_missing",
        "runtime_use_allowed",
        "live_use_allowed",
        "optimizer_use_allowed",
        "quantum_backend_use_allowed",
        "replay_paper_use_allowed",
        "research_use_allowed",
        "source_evidence_use_allowed",
        "blocks_qtt_when_owner_override_present",
    ):
        normalized[field] = _bool(normalized.get(field))
    return normalized


def _normalize_assignment_check(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_id": _string_or_none(check.get("check_id")),
        "parameter_family": _string_or_none(check.get("parameter_family")),
        "atomic_parameter_row_id": _string_or_none(check.get("atomic_parameter_row_id")),
        "row_pattern_id": _string_or_none(check.get("row_pattern_id")),
        "agent_role": _string_or_none(check.get("agent_role")),
        "agent_id": _string_or_none(check.get("agent_id")),
        "owner_override_token": _string_or_none(check.get("owner_override_token")),
        "expected_decision": _string_or_none(check.get("expected_decision")),
    }


def _normalize_registry(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: raw.get(field) for field in ROOT_FIELDS}
    normalized["schema_version"] = raw.get("schema_version")
    for field in (
        "registry_name",
        "registry_model",
        "authority_class",
        "source_master_plan",
        "final_expected_row_coverage",
    ):
        normalized[field] = str(normalized.get(field) or "")
    for field in (
        "canonical_source_for_parameter_agent_assignment",
        "deterministic_output",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "chatgpt_authority_over_owner",
        "codex_authority_over_owner",
        "qtt_agent_authority_over_owner",
        "validator_authority_over_owner",
        "generated_report_authority_over_owner",
        "static_gate_authority_over_owner",
        "uses_pr_number_as_authority",
    ):
        normalized[field] = _bool(normalized.get(field))
    for field in (
        "binding_statuses",
        "agent_roles",
        "consumer_classes",
        "agent_use_scopes",
        "lifecycle_statuses",
        "owner_override_tokens",
    ):
        normalized[field] = _string_list(normalized.get(field))
    normalized["authority_boundary"] = _normalize_authority_boundary(
        raw.get("authority_boundary")
    )
    bindings = raw.get("bindings")
    normalized["bindings"] = [
        _normalize_binding(binding)
        for binding in bindings
        if isinstance(binding, dict)
    ] if isinstance(bindings, list) else []
    for field in FIXTURE_FIELDS:
        if field in raw:
            normalized[field] = raw.get(field)
    if isinstance(raw.get("assignment_checks"), list):
        normalized["assignment_checks"] = [
            _normalize_assignment_check(check)
            for check in raw["assignment_checks"]
            if isinstance(check, dict)
        ]
    return normalized


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    raw = load_yaml_subset(path)
    return _normalize_registry(raw)


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"fixture root must be an object: {path}")
    return _normalize_registry(value)


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


def _uses_pr_number(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number(item) for item in value)
    return False


def _owner_satisfaction_present(binding: dict[str, Any]) -> bool:
    tokens = {
        binding.get("binding_authority_basis"),
        binding.get("owner_override_satisfaction_basis"),
        binding.get("final_qtt_internal_status"),
    }
    return binding.get("owner_override_applied") is True or bool(
        set(OWNER_OVERRIDE_TOKENS) & {str(token) for token in tokens if token}
    )


def _owner_override_present(binding: dict[str, Any]) -> bool:
    tokens = {
        binding.get("binding_authority_basis"),
        binding.get("owner_override_satisfaction_basis"),
        binding.get("final_qtt_internal_status"),
    }
    explicit_override_tokens = {
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
    }
    return binding.get("owner_override_applied") is True or bool(
        explicit_override_tokens & {str(token) for token in tokens if token}
    )


def _binding_identifier(binding: dict[str, Any], index: int = 0) -> str:
    binding_id = binding.get("binding_id")
    if _present_string(binding_id):
        return str(binding_id)
    return f"<missing-binding-id-{index}>"


def _binding_matches(
    binding: dict[str, Any],
    *,
    parameter_family: str | None = None,
    atomic_parameter_row_id: str | None = None,
    row_pattern_id: str | None = None,
) -> bool:
    if parameter_family and binding.get("parameter_family") == parameter_family:
        return True
    if atomic_parameter_row_id and binding.get("atomic_parameter_row_id") == atomic_parameter_row_id:
        return True
    if row_pattern_id and binding.get("row_pattern_id") == row_pattern_id:
        return True
    return False


def find_bindings_for_assignment(
    registry: dict[str, Any],
    *,
    parameter_family: str | None = None,
    atomic_parameter_row_id: str | None = None,
    row_pattern_id: str | None = None,
) -> list[dict[str, Any]]:
    return [
        binding
        for binding in registry.get("bindings", [])
        if isinstance(binding, dict)
        and _binding_matches(
            binding,
            parameter_family=parameter_family,
            atomic_parameter_row_id=atomic_parameter_row_id,
            row_pattern_id=row_pattern_id,
        )
    ]


def is_agent_assignment_allowed(
    registry: dict[str, Any],
    *,
    parameter_family: str | None = None,
    atomic_parameter_row_id: str | None = None,
    row_pattern_id: str | None = None,
    agent_role: str | None = None,
    agent_id: str | None = None,
    owner_override_token: str | None = None,
) -> AssignmentDecision:
    if owner_override_token in {"OWNER_GLOBAL_OVERRIDE", "AGENT_ASSIGNMENT_OWNER_APPROVED"}:
        return AssignmentDecision(
            True,
            "missing binding satisfied by owner global override or owner-approved assignment",
        )

    matches = find_bindings_for_assignment(
        registry,
        parameter_family=parameter_family,
        atomic_parameter_row_id=atomic_parameter_row_id,
        row_pattern_id=row_pattern_id,
    )
    if not matches:
        return AssignmentDecision(False, "missing binding blocked in normal mode")

    for binding in matches:
        owner_override = _owner_override_present(binding)
        if agent_role and agent_role in binding.get("blocked_agent_roles", []):
            if not owner_override:
                return AssignmentDecision(False, "agent role is explicitly blocked")
        if agent_id and agent_id in binding.get("blocked_agent_ids", []):
            if not owner_override:
                return AssignmentDecision(False, "agent id is explicitly blocked")
        if agent_role and agent_role in binding.get("authorized_agent_roles", []):
            return AssignmentDecision(True, "agent role is authorized by binding registry")
        if agent_id and agent_id in binding.get("authorized_agent_ids", []):
            return AssignmentDecision(True, "agent id is authorized by binding registry")
        if owner_override:
            if binding.get("blocks_qtt_when_owner_override_present") is True:
                continue
            return AssignmentDecision(True, "binding satisfied by owner override basis")
        if _owner_satisfaction_present(binding) and not (
            binding.get("authorized_agent_roles") or binding.get("authorized_agent_ids")
        ):
            return AssignmentDecision(True, "binding satisfied by owner authority basis")
    return AssignmentDecision(False, "binding exists but does not authorize this agent")


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    expectations = {
        "binding_status": list(BINDING_STATUSES),
        "agent_role": list(AGENT_ROLES),
        "consumer_class": list(CONSUMER_CLASSES),
        "agent_use_scope": list(AGENT_USE_SCOPES),
        "lifecycle_status": list(lifecycle_builder.LIFECYCLE_STATUSES),
        "owner_override_token": list(OWNER_OVERRIDE_TOKENS),
        "final_qtt_internal_status": list(FINAL_QTT_INTERNAL_STATUSES),
    }
    for name, expected in expectations.items():
        item = defs.get(name)
        if not isinstance(item, dict) or item.get("enum") != expected:
            failures.append(f"schema.$defs.{name} must contain the exact enum")

    binding = defs.get("binding")
    if isinstance(binding, dict):
        if binding.get("required") != list(BINDING_FIELDS):
            failures.append("schema.$defs.binding.required is not exact")
    else:
        failures.append("schema.$defs.binding must be an object")

    report_schema = defs.get("parameter_agent_binding_report")
    if isinstance(report_schema, dict):
        if report_schema.get("required") != list(_empty_report()):
            failures.append(
                "schema.$defs.parameter_agent_binding_report.required is not exact"
            )
    else:
        failures.append("schema.$defs.parameter_agent_binding_report must be an object")
    return failures


def validate_registry_shape(registry: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(registry, set(ROOT_FIELDS), "registry")
    expected_values: dict[str, Any] = {
        "schema_version": 1,
        "registry_name": REGISTRY_NAME,
        "registry_model": REGISTRY_MODEL,
        "authority_class": AUTHORITY_CLASS,
        "source_master_plan": "docs/master_plan/QTT_MasterPlan_Current.md",
        "canonical_source_for_parameter_agent_assignment": True,
        "deterministic_output": True,
        "owner_global_override_authority": True,
        "owner_override_satisfies_all_qtt_internal_requirements": True,
        "chatgpt_authority_over_owner": False,
        "codex_authority_over_owner": False,
        "qtt_agent_authority_over_owner": False,
        "validator_authority_over_owner": False,
        "generated_report_authority_over_owner": False,
        "static_gate_authority_over_owner": False,
        "uses_pr_number_as_authority": False,
        "binding_statuses": list(BINDING_STATUSES),
        "agent_roles": list(AGENT_ROLES),
        "consumer_classes": list(CONSUMER_CLASSES),
        "agent_use_scopes": list(AGENT_USE_SCOPES),
        "lifecycle_statuses": list(lifecycle_builder.LIFECYCLE_STATUSES),
        "owner_override_tokens": list(OWNER_OVERRIDE_TOKENS),
    }
    for field, expected in expected_values.items():
        if registry.get(field) != expected:
            failures.append(f"registry.{field} must be {expected}")

    if not isinstance(registry.get("bindings"), list) or not registry.get("bindings"):
        failures.append("registry.bindings must be a non-empty list")
    boundary = registry.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("registry.authority_boundary must be an object")
    else:
        failures.extend(
            _require_exact_fields(
                boundary,
                set(AUTHORITY_BOUNDARY_FIELDS),
                "registry.authority_boundary",
            )
        )
        for field in AUTHORITY_BOUNDARY_FIELDS:
            if boundary.get(field) is not False:
                failures.append(f"registry.authority_boundary.{field} must remain false")
    if _uses_pr_number(registry):
        failures.append("registry must not use a PR number as implementation authority")
    return failures


def validate_fixture_shape(fixture: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        set(ROOT_FIELDS) | set(FIXTURE_FIELDS),
        "fixture",
    )
    expected_values: dict[str, Any] = {
        "fixture_id": "SYNTHETIC_ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_FIXTURE",
        "fixture_version": "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_FIXTURE_V1",
        "fixture_authority_class": (
            "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_PARAMETER_AGENT_AUTHORITY"
        ),
        "schema_authority_class": (
            "STATIC_SCHEMA_CONTRACT_ONLY_NOT_PARAMETER_AGENT_AUTHORITY"
        ),
        "surface_kind": "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY_STATIC",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "validation_hook_ids": [VALIDATION_HOOK],
    }
    for field, expected in expected_values.items():
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    registry_view = {field: fixture.get(field) for field in ROOT_FIELDS}
    failures.extend(validate_registry_shape(registry_view))
    checks = fixture.get("assignment_checks")
    if not isinstance(checks, list) or not checks:
        failures.append("fixture.assignment_checks must be a non-empty list")
    else:
        seen: set[str] = set()
        for index, check in enumerate(checks):
            label = f"fixture.assignment_checks[{index}]"
            if not isinstance(check, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_exact_fields(
                    check,
                    {
                        "check_id",
                        "parameter_family",
                        "atomic_parameter_row_id",
                        "row_pattern_id",
                        "agent_role",
                        "agent_id",
                        "owner_override_token",
                        "expected_decision",
                    },
                    label,
                )
            )
            check_id = check.get("check_id")
            if not _present_string(check_id):
                failures.append(f"{label}.check_id must be a non-empty string")
            elif str(check_id) in seen:
                failures.append(f"{label}.check_id is duplicated")
            else:
                seen.add(str(check_id))
            if check.get("agent_role") not in AGENT_ROLES:
                failures.append(f"{label}.agent_role must be a known agent role")
            token = check.get("owner_override_token")
            if token is not None and token not in OWNER_OVERRIDE_TOKENS:
                failures.append(f"{label}.owner_override_token must be a known owner token")
            if check.get("expected_decision") not in {
                "ALLOWED_BY_BINDING",
                "BLOCKED_MISSING_BINDING",
                "OWNER_OVERRIDE_SATISFIED",
            }:
                failures.append(f"{label}.expected_decision is not allowed")
    if _uses_pr_number(fixture):
        failures.append("fixture must not use a PR number as implementation authority")
    return failures


def validate_bindings(bindings: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen_ids: set[str] = set()
    for index, binding in enumerate(bindings):
        label = f"bindings[{index}] {_binding_identifier(binding, index)}"
        failures.extend(_require_exact_fields(binding, set(BINDING_FIELDS), label))

        binding_id = binding.get("binding_id")
        if not _present_string(binding_id):
            failures.append(f"{label}.binding_id must be a non-empty string")
        elif str(binding_id) in seen_ids:
            failures.append(f"{label}: duplicate binding_id {binding_id}")
        else:
            seen_ids.add(str(binding_id))

        if binding.get("binding_status") not in BINDING_STATUSES:
            failures.append(f"{label}.binding_status is not allowed")
        if binding.get("binding_authority_basis") not in OWNER_OVERRIDE_TOKENS:
            failures.append(f"{label}.binding_authority_basis is not an owner token")

        owner_satisfaction = _owner_satisfaction_present(binding)
        owner_override = _owner_override_present(binding)

        if not _present_string(binding.get("parameter_family")) and not _present_string(
            binding.get("owner_approved_value")
        ):
            failures.append(
                f"{label}.parameter_family is missing without owner-approved value"
            )
        if not any(
            _present_string(binding.get(field))
            for field in (
                "parameter_family",
                "atomic_parameter_row_id",
                "row_pattern_id",
            )
        ):
            failures.append(
                f"{label}: one of parameter_family, atomic_parameter_row_id, "
                "or row_pattern_id must be present"
            )

        owning_agent = binding.get("owning_agent_role")
        if owning_agent is not None and owning_agent not in AGENT_ROLES:
            failures.append(f"{label}.owning_agent_role is not a known agent role")
        if owning_agent is None and not owner_satisfaction:
            failures.append(
                f"{label}.owning_agent_role may be missing only with owner satisfaction"
            )

        for field in ("authorized_agent_roles", "blocked_agent_roles"):
            for role in binding.get(field, []):
                if role not in AGENT_ROLES:
                    failures.append(f"{label}.{field} has unknown agent role {role}")
        for field in ("authorized_consumer_classes", "blocked_consumer_classes"):
            for consumer_class in binding.get(field, []):
                if consumer_class not in CONSUMER_CLASSES:
                    failures.append(
                        f"{label}.{field} has unknown consumer class {consumer_class}"
                    )
        if binding.get("agent_use_scope") not in AGENT_USE_SCOPES:
            failures.append(f"{label}.agent_use_scope is not allowed")
        lifecycle_status = binding.get("requires_lifecycle_status_at_least")
        if lifecycle_status is not None and lifecycle_status not in lifecycle_builder.LIFECYCLE_STATUSES:
            failures.append(
                f"{label}.requires_lifecycle_status_at_least is not allowed"
            )
        if binding.get("final_qtt_internal_status") not in FINAL_QTT_INTERNAL_STATUSES:
            failures.append(f"{label}.final_qtt_internal_status is not allowed")

        if not binding.get("authorized_agent_roles") and not binding.get(
            "authorized_agent_ids"
        ) and not owner_satisfaction:
            failures.append(
                f"{label}: authorized_agent_roles and authorized_agent_ids are "
                "both empty without owner satisfaction"
            )
        if not binding.get("authorized_consumer_classes") and not owner_satisfaction:
            failures.append(
                f"{label}: authorized_consumer_classes is empty without owner satisfaction"
            )

        if owner_override:
            if binding.get("blocks_qtt_when_owner_override_present") is True:
                failures.append(
                    f"{label}: owner override may not block QTT internal workflow"
                )
            if binding.get("final_qtt_internal_status") not in OWNER_OVERRIDE_FINAL_STATUSES:
                failures.append(
                    f"{label}: owner override final status is not owner-satisfied"
                )

        if binding.get("owner_override_applied") is True:
            if binding.get("blocks_qtt_when_owner_override_present") is True:
                failures.append(
                    f"{label}: owner_override_applied requires nonblocking status"
                )
            if binding.get("final_qtt_internal_status") not in OWNER_OVERRIDE_FINAL_STATUSES:
                failures.append(
                    f"{label}: owner_override_applied has invalid final status"
                )

        if binding.get("requires_owner_override_when_missing") is True and not owner_satisfaction:
            failures.append(
                f"{label}: missing prerequisites require owner satisfaction basis"
            )

        status = binding.get("binding_status")
        scope = binding.get("agent_use_scope")
        lifecycle = binding.get("requires_lifecycle_status_at_least")
        quarantine_or_retired = (
            status in {"QUARANTINED_BINDING", "RETIRED_BINDING"}
            or scope in {"QUARANTINE_REVIEW_ONLY", "RETIREMENT_AUDIT_ONLY"}
            or lifecycle in {"QUARANTINED_UNPROVEN", "RETIRED_NOT_USEFUL"}
        )
        if quarantine_or_retired and not owner_override:
            unauthorized_roles = set(binding.get("authorized_agent_roles", [])) - QUARANTINE_REVIEW_ROLES
            if unauthorized_roles:
                failures.append(
                    f"{label}: quarantined or retired families may bind only to "
                    "governance/validation roles without owner override"
                )

        if binding.get("live_use_allowed") is True and binding.get(
            "optimizer_use_allowed"
        ) is True:
            failures.append(
                f"{label}: optimizer binding must not imply live/order authority"
            )
    return failures


def _authority_boundary_all_false(registry: dict[str, Any]) -> bool:
    boundary = _mapping(registry.get("authority_boundary"))
    root_authority_fields = (
        "chatgpt_authority_over_owner",
        "codex_authority_over_owner",
        "qtt_agent_authority_over_owner",
        "validator_authority_over_owner",
        "generated_report_authority_over_owner",
        "static_gate_authority_over_owner",
    )
    return all(boundary.get(field) is False for field in AUTHORITY_BOUNDARY_FIELDS) and all(
        registry.get(field) is False for field in root_authority_fields
    )


def _evaluate_assignment_checks(
    registry: dict[str, Any],
    fixture: dict[str, Any],
) -> tuple[int, int, list[str]]:
    normal_blocked = 0
    owner_override_satisfied = 0
    failures: list[str] = []
    checks = fixture.get("assignment_checks", [])
    if not isinstance(checks, list):
        return 0, 0, ["fixture.assignment_checks must be a list"]
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            continue
        decision = is_agent_assignment_allowed(
            registry,
            parameter_family=check.get("parameter_family"),
            atomic_parameter_row_id=check.get("atomic_parameter_row_id"),
            row_pattern_id=check.get("row_pattern_id"),
            agent_role=check.get("agent_role"),
            agent_id=check.get("agent_id"),
            owner_override_token=check.get("owner_override_token"),
        )
        expected = check.get("expected_decision")
        if expected == "BLOCKED_MISSING_BINDING":
            normal_blocked += 1
            if decision.allowed is not False:
                failures.append(
                    f"assignment_checks[{index}] expected normal missing binding block"
                )
        elif expected == "OWNER_OVERRIDE_SATISFIED":
            owner_override_satisfied += 1
            if decision.allowed is not True:
                failures.append(
                    f"assignment_checks[{index}] expected owner override satisfaction"
                )
        elif expected == "ALLOWED_BY_BINDING":
            if decision.allowed is not True:
                failures.append(f"assignment_checks[{index}] expected binding allowance")
        else:
            failures.append(f"assignment_checks[{index}] has unknown expected decision")
    return normal_blocked, owner_override_satisfied, failures


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "binding_count": 0,
        "parameter_family_binding_count": 0,
        "row_level_binding_count": 0,
        "pattern_level_binding_count": 0,
        "agent_role_count": 0,
        "agent_id_count": 0,
        "authorized_agent_role_binding_count": 0,
        "blocked_agent_role_binding_count": 0,
        "authorized_consumer_class_binding_count": 0,
        "blocked_consumer_class_binding_count": 0,
        "owner_approved_binding_count": 0,
        "owner_global_override_binding_count": 0,
        "owner_override_satisfied_binding_count": 0,
        "missing_binding_normal_blocked_count": 0,
        "missing_binding_owner_override_satisfied_count": 0,
        "runtime_binding_count": 0,
        "live_binding_count": 0,
        "quantum_backend_binding_count": 0,
        "real_runtime_artifact_created": False,
        "real_live_artifact_created": False,
        "real_order_artifact_created": False,
        "real_quantum_backend_artifact_created": False,
        "real_profit_artifact_created": False,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "uses_pr_number_as_authority": False,
        "final_ready": False,
        "authority_boundary_all_false": False,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    registry: dict[str, Any],
    fixture: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    bindings = sorted(registry.get("bindings", []), key=lambda item: item.get("binding_id") or "")
    authority_boundary = _mapping(registry.get("authority_boundary"))
    normal_blocked = 0
    owner_override_missing_satisfied = 0
    failures: list[str] = []
    if fixture is not None:
        normal_blocked, owner_override_missing_satisfied, failures = (
            _evaluate_assignment_checks(registry, fixture)
        )

    agent_roles: set[str] = set()
    agent_ids: set[str] = set()
    for binding in bindings:
        if _present_string(binding.get("owning_agent_role")):
            agent_roles.add(str(binding["owning_agent_role"]))
        agent_roles.update(binding.get("authorized_agent_roles", []))
        agent_roles.update(binding.get("blocked_agent_roles", []))
        agent_ids.update(binding.get("authorized_agent_ids", []))
        agent_ids.update(binding.get("blocked_agent_ids", []))

    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "binding_count": len(bindings),
        "parameter_family_binding_count": sum(
            1 for binding in bindings if _present_string(binding.get("parameter_family"))
        ),
        "row_level_binding_count": sum(
            1
            for binding in bindings
            if _present_string(binding.get("atomic_parameter_row_id"))
        ),
        "pattern_level_binding_count": sum(
            1 for binding in bindings if _present_string(binding.get("row_pattern_id"))
        ),
        "agent_role_count": len(agent_roles),
        "agent_id_count": len(agent_ids),
        "authorized_agent_role_binding_count": sum(
            len(binding.get("authorized_agent_roles", [])) for binding in bindings
        ),
        "blocked_agent_role_binding_count": sum(
            len(binding.get("blocked_agent_roles", [])) for binding in bindings
        ),
        "authorized_consumer_class_binding_count": sum(
            len(binding.get("authorized_consumer_classes", [])) for binding in bindings
        ),
        "blocked_consumer_class_binding_count": sum(
            len(binding.get("blocked_consumer_classes", [])) for binding in bindings
        ),
        "owner_approved_binding_count": sum(
            1
            for binding in bindings
            if binding.get("binding_status") == "OWNER_APPROVED_BINDING"
        ),
        "owner_global_override_binding_count": sum(
            1
            for binding in bindings
            if binding.get("binding_status") == "OWNER_GLOBAL_OVERRIDE_BINDING"
            or binding.get("binding_authority_basis") == "OWNER_GLOBAL_OVERRIDE"
        ),
        "owner_override_satisfied_binding_count": sum(
            1
            for binding in bindings
            if binding.get("final_qtt_internal_status") == "OWNER_OVERRIDE_SATISFIED"
            or binding.get("owner_override_satisfaction_basis")
            in {"OWNER_OVERRIDE_SATISFIED", "AGENT_ASSIGNMENT_OWNER_APPROVED"}
        ),
        "missing_binding_normal_blocked_count": normal_blocked,
        "missing_binding_owner_override_satisfied_count": owner_override_missing_satisfied,
        "runtime_binding_count": sum(
            1 for binding in bindings if binding.get("runtime_use_allowed") is True
        ),
        "live_binding_count": sum(
            1 for binding in bindings if binding.get("live_use_allowed") is True
        ),
        "quantum_backend_binding_count": sum(
            1
            for binding in bindings
            if binding.get("quantum_backend_use_allowed") is True
        ),
        "real_runtime_artifact_created": authority_boundary.get(
            "real_runtime_artifact_created"
        )
        is True,
        "real_live_artifact_created": authority_boundary.get("real_live_artifact_created")
        is True,
        "real_order_artifact_created": authority_boundary.get(
            "real_order_artifact_created"
        )
        is True,
        "real_quantum_backend_artifact_created": authority_boundary.get(
            "real_quantum_backend_artifact_created"
        )
        is True,
        "real_profit_artifact_created": authority_boundary.get(
            "real_profit_artifact_created"
        )
        is True,
        "bundle_file_present": (repo_root / CANONICAL_BUNDLE).exists(),
        "bundle_sha_present": (repo_root / CANONICAL_BUNDLE_SHA).exists(),
        "uses_pr_number_as_authority": registry.get("uses_pr_number_as_authority") is True
        or _uses_pr_number(registry),
        "final_ready": False,
        "authority_boundary_all_false": _authority_boundary_all_false(registry),
    }
    return report, failures


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(schema.get("$defs")).get("parameter_agent_binding_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.parameter_agent_binding_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_false_fields = (
        "real_runtime_artifact_created",
        "real_live_artifact_created",
        "real_order_artifact_created",
        "real_quantum_backend_artifact_created",
        "real_profit_artifact_created",
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )
    for field in expected_false_fields:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("authority_boundary_all_false") is not True:
        failures.append("report.authority_boundary_all_false must be true")
    if report.get("binding_count", 0) < 12:
        failures.append("report.binding_count must be at least 12")
    if report.get("owner_approved_binding_count", 0) < 5:
        failures.append("report.owner_approved_binding_count must be at least 5")
    if report.get("owner_global_override_binding_count", 0) < 3:
        failures.append("report.owner_global_override_binding_count must be at least 3")
    if report.get("owner_override_satisfied_binding_count", 0) < 3:
        failures.append(
            "report.owner_override_satisfied_binding_count must be at least 3"
        )
    if report.get("missing_binding_owner_override_satisfied_count", 0) < 1:
        failures.append(
            "report.missing_binding_owner_override_satisfied_count must be at least 1"
        )
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
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
    try:
        registry = load_registry(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    try:
        fixture = load_fixture(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    schema, schema_failures = _load_json(root / schema_path)
    fixture_json, fixture_json_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_json_failures)

    if schema is not None:
        failures.extend(validate_json_schema_subset(registry, schema))
        if fixture_json is not None:
            failures.extend(validate_json_schema_subset(fixture_json, schema))
        failures.extend(_validate_schema_surface(schema))

    failures.extend(validate_registry_shape(registry))
    failures.extend(validate_fixture_shape(fixture))
    failures.extend(validate_bindings(registry.get("bindings", [])))
    failures.extend(validate_bindings(fixture.get("bindings", [])))

    report, report_failures = build_report(
        repo_root=root,
        registry=registry,
        fixture=fixture,
    )
    failures.extend(report_failures)
    second_report, _ = build_report(repo_root=root, registry=registry, fixture=fixture)
    if report != second_report:
        failures.append("generated parameter-agent binding report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if output_path is not None:
        output = root / output_path
        if output.exists():
            try:
                actual = json.loads(output.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"generated report is invalid JSON: {output_path}: {exc}")
            else:
                if actual != report:
                    failures.append(
                        "generated report is stale or non-deterministic: "
                        f"{output_path.as_posix()}"
                    )

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows parameter-agent binding registry is "
            "a static foundation, not complete 4,183-row coverage"
        )

    if output_path is not None and not failures:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
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
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"bindings={report.get('binding_count', 0)} "
            f"owner_approved={report.get('owner_approved_binding_count', 0)} "
            f"owner_global_override="
            f"{report.get('owner_global_override_binding_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
