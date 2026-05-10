#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Iterable, Sequence

SUCCESS_MARKER = "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_VALIDATION_OK"
FAILURE_MARKER = "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_VALIDATION_FAILED"
REPORT_TYPE = "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT"
DETERMINISTIC_CREATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
VALIDATION_HOOK = "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_STATIC_VALIDATION"

DEFAULT_GLOBAL_SCHEMA = pathlib.Path(
    "schemas/governance/qtt_owner_global_override_authority.schema.json"
)
DEFAULT_RECEIPT_SCHEMA = pathlib.Path(
    "schemas/governance/qtt_owner_override_receipt.schema.json"
)
DEFAULT_APPROVAL_REQUEST_SCHEMA = pathlib.Path(
    "schemas/governance/qtt_owner_approval_request.schema.json"
)
DEFAULT_POLICY = pathlib.Path(
    "docs/master_plan/governance/QTTOwnerGlobalOverrideAuthority.yaml"
)
DEFAULT_AUTHORITY_FIXTURE = pathlib.Path(
    "tests/fixtures/governance/"
    "synthetic_qtt_owner_global_override_authority.v1.fixture.json"
)
DEFAULT_RECEIPT_FIXTURE = pathlib.Path(
    "tests/fixtures/governance/synthetic_qtt_owner_override_receipt.v1.fixture.json"
)
DEFAULT_APPROVAL_REQUEST_FIXTURE = pathlib.Path(
    "tests/fixtures/governance/synthetic_qtt_owner_approval_request.v1.fixture.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json"
)

OWNER_APPROVED_VALUE_TOKENS: tuple[str, ...] = (
    "OWNER_APPROVED",
    "OWNER_APPROVED_OVERRIDE",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED_NOT_EXTERNALLY_VERIFIED",
    "OWNER_APPROVED_UNVERIFIED",
    "OWNER_RISK_ACCEPTED",
    "OWNER_ASSUMED_RESPONSIBILITY",
    "OWNER_WAIVED_REQUIREMENT",
    "OWNER_APPROVED_VALUE",
    "OWNER_APPROVED_MISSING_VALUE",
    "OWNER_APPROVED_NOT_SOURCE_BACKED",
    "OWNER_APPROVED_NOT_RECEIPT_BACKED",
    "OWNER_APPROVED_NOT_RUNTIME_VERIFIED",
    "OWNER_APPROVED_NOT_LIVE_VERIFIED",
    "OWNER_APPROVED_NOT_QUANTUM_BACKEND_VERIFIED",
    "EVIDENCE_NOT_REQUIRED_BY_OWNER_POLICY",
    "SOURCE_EVIDENCE_REQUIREMENT_SATISFIED_BY_OWNER_OVERRIDE",
    "FINAL_READINESS_BLOCKER_SATISFIED_BY_OWNER_OVERRIDE",
    "VALIDATION_BLOCKER_SATISFIED_BY_OWNER_OVERRIDE",
    "COMPLIANCE_MARKER_OWNER_APPROVED",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
    "OPTIMIZER_ADMISSION_OWNER_APPROVED",
    "RUNTIME_ADMISSION_OWNER_APPROVED",
    "LIVE_USE_ADMISSION_OWNER_APPROVED",
    "QUANTUM_BACKEND_REQUIREMENT_OWNER_APPROVED",
    "REPLAY_PAPER_REQUIREMENT_OWNER_APPROVED",
    "ROW_COMPLETION_OWNER_APPROVED",
    "CONNECTOR_BINDING_OWNER_APPROVED",
    "RUNTIME_RESOLVER_OWNER_APPROVED",
    "LIVE_CANARY_OWNER_APPROVED",
    "GENERATED_REPORT_REQUIREMENT_OWNER_APPROVED",
    "PROMOTION_BLOCKER_OWNER_APPROVED",
    "MUTATION_BLOCKER_OWNER_APPROVED",
    "FINAL_MODE_BLOCKER_OWNER_APPROVED",
)

OWNER_DECISION_OPTIONS: tuple[str, ...] = (
    "APPROVE",
    "APPROVE_WITH_OVERRIDE",
    "APPROVE_GLOBAL_OVERRIDE",
    "REJECT",
    "REQUEST_MORE_INFO",
    "WAIVE_REQUIREMENT",
    "SET_OWNER_APPROVED_VALUE",
    "SET_OWNER_GLOBAL_OVERRIDE",
    "APPROVE_RESEARCH_ONLY",
    "APPROVE_REPLAY_ONLY",
    "APPROVE_PAPER_ONLY",
    "APPROVE_REPLAY_PAPER",
    "APPROVE_OPTIMIZER",
    "APPROVE_RUNTIME",
    "APPROVE_LIVE_USE",
    "APPROVE_QUANTUM_BACKEND",
    "APPROVE_SOURCE_EVIDENCE_OVERRIDE",
    "APPROVE_FINAL_READINESS_OVERRIDE",
    "APPROVE_VALIDATION_BLOCKER_OVERRIDE",
    "APPLY_TO_ONE_ROW",
    "APPLY_TO_PARAMETER_FAMILY",
    "APPLY_TO_AGENT",
    "APPLY_TO_DOMAIN",
    "APPLY_GLOBALLY",
)

REQUIRED_DOMAINS: tuple[str, ...] = (
    "ATOMICROWS",
    "SOURCE_EVIDENCE",
    "SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION",
    "OWNER_SUBMITTED_RESEARCH_SOURCES",
    "AGENT_ASSIGNMENT",
    "OPTIMIZER",
    "OPTIMIZER_ADMISSION",
    "RUNTIME_ADMISSION",
    "LIVE_USE_ADMISSION",
    "QUANTUM_BACKEND",
    "REPLAY_PAPER",
    "FINAL_READINESS",
    "VALIDATION_GATES",
    "GENERATED_REPORTS",
    "ROW_COMPLETION",
    "MISSING_REQUIRED_VALUES",
    "COMPLIANCE_MARKERS",
    "CONNECTOR_BINDING",
    "RUNTIME_RESOLVER",
    "LIVE_CANARY",
    "PROMOTION",
    "MUTATION",
    "FINAL_MODE",
    "DASHBOARD_OWNER_APPROVAL_REQUESTS",
    "QTT_AGENT_APPROVAL_REQUESTS",
    "ORDER_AUTHORITY",
    "RUNTIME_CASH",
    "PROFIT_EVIDENCE",
)

REQUIRED_REQUIREMENT_CLASSES: tuple[str, ...] = (
    "ATOMICROWS_LIFECYCLE_STATUS_REQUIREMENT",
    "ATOMICROWS_PARAMETER_ROW_COMPLETION_REQUIREMENT",
    "ATOMICROWS_SOURCE_EVIDENCE_REQUIREMENT",
    "ATOMICROWS_AGENT_BINDING_REQUIREMENT",
    "ATOMICROWS_OPTIMIZER_ADMISSION_REQUIREMENT",
    "ATOMICROWS_RUNTIME_ADMISSION_REQUIREMENT",
    "ATOMICROWS_LIVE_USE_ADMISSION_REQUIREMENT",
    "ATOMICROWS_FINAL_READINESS_BLOCKER",
    "ATOMICROWS_MISSING_REQUIRED_VALUE_REQUIREMENT",
    "ATOMICROWS_PROMOTION_BLOCKER_REQUIREMENT",
    "ATOMICROWS_MUTATION_BLOCKER_REQUIREMENT",
    "SOURCE_EVIDENCE_ACCEPTANCE_REQUIREMENT",
    "SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION",
    "OWNER_SUBMITTED_RESEARCH_SOURCE_REQUIREMENT",
    "CONNECTOR_BINDING_REQUIREMENT",
    "CONNECTOR_BINDING_READINESS_MARKER",
    "RUNTIME_RESOLVER_REQUIREMENT",
    "RUNTIME_RESOLVER_READINESS_MARKER",
    "REPLAY_PAPER_REQUIREMENT",
    "REPLAY_PAPER_RECEIPT_REQUIREMENT",
    "OPTIMIZER_REQUIREMENT",
    "OPTIMIZER_ADMISSION_REQUIREMENT",
    "QUANTUM_BACKEND_REQUIREMENT",
    "QUANTUM_BACKEND_EVIDENCE_REQUIREMENT",
    "LIVE_CANARY_REQUIREMENT",
    "LIVE_CANARY_READINESS_MARKER",
    "LIVE_USE_ADMISSION_REQUIREMENT",
    "ORDER_AUTHORITY_REQUIREMENT",
    "RUNTIME_CASH_RECEIPT_REQUIREMENT",
    "PROFIT_EVIDENCE_REQUIREMENT",
    "COMPLIANCE_MARKER_REQUIREMENT",
    "VALIDATION_GATE_REQUIREMENT",
    "GENERATED_REPORT_REQUIREMENT",
    "FINAL_READINESS_BLOCKER_REQUIREMENT",
    "FINAL_MODE_BLOCKER_REQUIREMENT",
    "MISSING_REQUIRED_VALUE_REQUIREMENT",
    "DASHBOARD_OWNER_APPROVAL_REQUEST_REQUIREMENT",
    "AGENT_OWNER_APPROVAL_REQUEST_REQUIREMENT",
)

AUTHORITY_TRUE_FIELDS: tuple[str, ...] = (
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_is_sole_final_internal_workflow_authority",
    "validators_must_not_block_owner_override",
    "codex_must_not_block_owner_override",
    "chatgpt_must_not_block_owner_override",
    "qtt_agents_must_not_block_owner_override",
    "generated_reports_must_not_block_owner_override",
    "validation_gates_must_not_block_owner_override",
    "owner_override_applies_to_all_qtt_domains",
    "owner_override_applies_to_all_qtt_internal_requirements",
    "owner_override_applies_to_missing_required_values",
    "owner_override_applies_to_source_evidence_requirements",
    "owner_override_applies_to_final_readiness_blockers",
    "owner_override_applies_to_validation_blockers",
)

AUTHORITY_FALSE_FIELDS: tuple[str, ...] = (
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "validator_authority_over_owner",
    "generated_report_authority_over_owner",
    "qtt_gate_authority_over_owner",
)

REQUIREMENT_MODEL_FIELDS: tuple[str, ...] = (
    "requirement_id",
    "requirement_class",
    "domain",
    "normal_requirement_status",
    "owner_override_allowed",
    "owner_override_applied",
    "owner_override_satisfaction_basis",
    "owner_approved_value",
    "blocks_qtt_when_owner_override_present",
    "externally_verified_status",
    "artifact_exists_status",
    "receipt_exists_status",
    "final_qtt_internal_status",
    "owner_override_scope",
    "owner_override_reason",
    "owner_override_recording_mode",
    "owner_override_receipt_required",
    "owner_override_receipt_id",
    "owner_override_receipt_locator",
    "owner_approval_request_supported",
    "future_dashboard_action_supported",
)

RECEIPT_FIELDS: tuple[str, ...] = (
    "owner_override_id",
    "authority",
    "owner_decision",
    "owner_decision_options",
    "applies_to_domain",
    "applies_to_requirement_class",
    "applies_to_target",
    "owner_approved_value",
    "owner_override_satisfaction_basis",
    "final_qtt_internal_status",
    "blocks_qtt_when_owner_override_present",
    "approval_scope",
    "owner_note",
    "created_by_owner",
    "deterministic_created_at_utc",
    "receipt_locator",
    "receipt_status",
    "future_dashboard_source_supported",
    "future_agent_request_source_supported",
)

APPROVAL_REQUEST_FIELDS: tuple[str, ...] = (
    "request_id",
    "requesting_agent",
    "requested_action",
    "requested_owner_decision_options",
    "target_domain",
    "target_requirement_class",
    "target_parameter_family",
    "target_atomic_parameter_row_id",
    "target_agent_id",
    "target_gate",
    "normal_blocker",
    "requested_override_basis",
    "recommended_scope",
    "requester_reason",
    "owner_decision_pending",
    "agent_may_approve_for_owner",
    "codex_may_approve_for_owner",
    "chatgpt_may_approve_for_owner",
    "future_dashboard_menu_supported",
    "deterministic_created_at_utc",
)

FINAL_STATUS_TOKENS = {
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_APPROVED_OVERRIDE",
}

AUTHORITY_BOUNDARY_FALSE_FIELDS: tuple[str, ...] = (
    "creates_dashboard_ui",
    "creates_runtime_service",
    "creates_live_trading_execution",
    "creates_real_source_acceptance_artifact",
    "creates_real_connector_binding_artifact",
    "creates_real_runtime_receipts",
    "creates_real_live_receipts",
    "creates_order_receipts",
    "creates_cash_receipts",
    "creates_sha_freeze_authority",
    "creates_profit_evidence",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_sha256",
)


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _parse_policy_yaml(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"policy YAML file is missing: {path}"]
    policy: dict[str, Any] = {}
    active_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  - ") and active_list_key is not None:
            policy.setdefault(active_list_key, []).append(raw_line[4:].strip())
            continue
        active_list_key = None
        if ":" not in raw_line or raw_line.startswith(" "):
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            policy[key] = []
            active_list_key = key
        elif value == "true":
            policy[key] = True
        elif value == "false":
            policy[key] = False
        else:
            policy[key] = value
    return policy, []


def _properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _defs(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs", {})
    return defs if isinstance(defs, dict) else {}


def _required(definition: dict[str, Any]) -> set[str]:
    required = definition.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _const(definition: dict[str, Any], field: str) -> Any:
    prop = _properties(definition).get(field, {})
    return prop.get("const") if isinstance(prop, dict) else None


def _enum(definition: dict[str, Any], def_name: str) -> set[str]:
    item = _defs(definition).get(def_name, {})
    enum = item.get("enum") if isinstance(item, dict) else None
    return set(enum) if isinstance(enum, list) else set()


def _require_fields(value: dict[str, Any], fields: Iterable[str], label: str) -> list[str]:
    missing = sorted(set(fields) - set(value))
    return [f"{label} missing required fields: {', '.join(missing)}"] if missing else []


def _list_value(value: dict[str, Any], field: str, label: str) -> tuple[list[Any], list[str]]:
    item = value.get(field)
    if not isinstance(item, list):
        return [], [f"{label}.{field} must be a list"]
    return item, []


def _records_by_class(fixture: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {}
    cases = fixture.get("requirement_satisfaction_cases", [])
    if not isinstance(cases, list):
        return records
    for item in cases:
        if isinstance(item, dict) and isinstance(item.get("requirement_class"), str):
            records.setdefault(item["requirement_class"], []).append(item)
    return records


def _has_case(
    fixture: dict[str, Any],
    requirement_class: str,
    *,
    basis: str | None = None,
    owner_value: str | None = None,
) -> bool:
    for record in _records_by_class(fixture).get(requirement_class, []):
        if basis is not None and record.get("owner_override_satisfaction_basis") != basis:
            continue
        if owner_value is not None and record.get("owner_approved_value") != owner_value:
            continue
        if record.get("owner_override_applied") is True:
            return True
    return False


def _schema_common_failures(schema: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{label}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{label}.additionalProperties must be false")
    for field in AUTHORITY_TRUE_FIELDS:
        if field in _properties(schema) and _const(schema, field) is not True:
            failures.append(f"{label}.{field} must be const true")
    for field in AUTHORITY_FALSE_FIELDS:
        if field in _properties(schema) and _const(schema, field) is not False:
            failures.append(f"{label}.{field} must be const false")
    return failures


def validate_global_schema(schema: dict[str, Any]) -> list[str]:
    failures = _schema_common_failures(schema, "global schema")
    required = _required(schema)
    for field in (
        set(AUTHORITY_TRUE_FIELDS)
        | set(AUTHORITY_FALSE_FIELDS)
        | {
            "owner_approved_value_tokens",
            "owner_decision_options",
            "covered_domains",
            "covered_requirement_classes",
            "requirement_satisfaction_cases",
            "authority_boundary",
            "authority_boundary_all_false",
            "uses_pr_number_as_authority",
        }
    ):
        if field not in required:
            failures.append(f"global schema must require {field}")
    missing_tokens = sorted(set(OWNER_APPROVED_VALUE_TOKENS) - _enum(schema, "owner_approved_value_token"))
    if missing_tokens:
        failures.append(f"global schema token enum missing: {', '.join(missing_tokens)}")
    missing_options = sorted(set(OWNER_DECISION_OPTIONS) - _enum(schema, "owner_decision_option"))
    if missing_options:
        failures.append(f"global schema decision enum missing: {', '.join(missing_options)}")
    missing_classes = sorted(set(REQUIRED_REQUIREMENT_CLASSES) - _enum(schema, "covered_requirement_class"))
    if missing_classes:
        failures.append(f"global schema requirement enum missing: {', '.join(missing_classes)}")

    case_def = _defs(schema).get("requirement_satisfaction_case", {})
    if not isinstance(case_def, dict):
        failures.append("global schema missing requirement_satisfaction_case definition")
    else:
        missing_model_fields = sorted(set(REQUIREMENT_MODEL_FIELDS) - _required(case_def))
        if missing_model_fields:
            failures.append(
                "global schema requirement case missing fields: "
                + ", ".join(missing_model_fields)
            )
    boundary_def = _defs(schema).get("authority_boundary", {})
    if isinstance(boundary_def, dict):
        for field in AUTHORITY_BOUNDARY_FALSE_FIELDS + ("uses_pr_number_as_authority",):
            if _const(boundary_def, field) is not False:
                failures.append(f"global schema authority_boundary.{field} must be const false")
    else:
        failures.append("global schema missing authority_boundary definition")
    return failures


def validate_receipt_schema(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    receipt_def = _defs(schema).get("owner_override_receipt", {})
    if not isinstance(receipt_def, dict):
        return ["receipt schema missing owner_override_receipt definition"]
    missing_fields = sorted(set(RECEIPT_FIELDS) - _required(receipt_def))
    if missing_fields:
        failures.append(f"receipt schema missing fields: {', '.join(missing_fields)}")
    if _const(receipt_def, "authority") != "OWNER_GLOBAL_OVERRIDE":
        failures.append("receipt schema authority must be const OWNER_GLOBAL_OVERRIDE")
    if _const(receipt_def, "blocks_qtt_when_owner_override_present") is not False:
        failures.append("receipt schema owner override must not block QTT")
    if _const(receipt_def, "created_by_owner") is not True:
        failures.append("receipt schema created_by_owner must be const true")
    missing_options = sorted(set(OWNER_DECISION_OPTIONS) - _enum(schema, "owner_decision_option"))
    if missing_options:
        failures.append(f"receipt schema decision enum missing: {', '.join(missing_options)}")
    missing_tokens = sorted(set(OWNER_APPROVED_VALUE_TOKENS) - _enum(schema, "owner_approved_value_token"))
    if missing_tokens:
        failures.append(f"receipt schema token enum missing: {', '.join(missing_tokens)}")
    return failures


def validate_approval_request_schema(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    request_def = _defs(schema).get("owner_approval_request", {})
    if not isinstance(request_def, dict):
        return ["approval request schema missing owner_approval_request definition"]
    missing_fields = sorted(set(APPROVAL_REQUEST_FIELDS) - _required(request_def))
    if missing_fields:
        failures.append(f"approval request schema missing fields: {', '.join(missing_fields)}")
    for field in (
        "owner_decision_pending",
        "future_dashboard_menu_supported",
    ):
        if _const(request_def, field) is not True:
            failures.append(f"approval request schema {field} must be const true")
    for field in (
        "agent_may_approve_for_owner",
        "codex_may_approve_for_owner",
        "chatgpt_may_approve_for_owner",
    ):
        if _const(request_def, field) is not False:
            failures.append(f"approval request schema {field} must be const false")
    missing_options = sorted(set(OWNER_DECISION_OPTIONS) - _enum(schema, "owner_decision_option"))
    if missing_options:
        failures.append(f"approval request schema decision enum missing: {', '.join(missing_options)}")
    missing_tokens = sorted(set(OWNER_APPROVED_VALUE_TOKENS) - _enum(schema, "owner_approved_value_token"))
    if missing_tokens:
        failures.append(f"approval request schema token enum missing: {', '.join(missing_tokens)}")
    return failures


def validate_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in AUTHORITY_TRUE_FIELDS:
        if policy.get(field) is not True:
            failures.append(f"policy.{field} must be true")
    for field in AUTHORITY_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"policy.{field} must be false")
    for field in (
        "future_dashboard_menu_supported",
        "future_agent_approval_request_supported",
        "authority_boundary_all_false",
    ):
        if policy.get(field) is not True:
            failures.append(f"policy.{field} must be true")
    for field in (
        "agent_may_approve_for_owner",
        "codex_may_approve_for_owner",
        "chatgpt_may_approve_for_owner",
        "uses_pr_number_as_authority",
        *AUTHORITY_BOUNDARY_FALSE_FIELDS,
    ):
        if policy.get(field) is not False:
            failures.append(f"policy.{field} must be false")
    expected_lists = {
        "owner_approved_value_tokens": OWNER_APPROVED_VALUE_TOKENS,
        "owner_decision_options": OWNER_DECISION_OPTIONS,
        "covered_domains": REQUIRED_DOMAINS,
        "covered_requirement_classes": REQUIRED_REQUIREMENT_CLASSES,
    }
    for field, expected in expected_lists.items():
        values = policy.get(field)
        if not isinstance(values, list):
            failures.append(f"policy.{field} must be a list")
            continue
        missing = sorted(set(expected) - set(values))
        if missing:
            failures.append(f"policy.{field} missing: {', '.join(missing)}")
    return failures


def validate_authority_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in AUTHORITY_TRUE_FIELDS:
        if fixture.get(field) is not True:
            failures.append(f"authority fixture.{field} must be true")
    for field in AUTHORITY_FALSE_FIELDS:
        if fixture.get(field) is not False:
            failures.append(f"authority fixture.{field} must be false")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("authority fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("authority fixture.execution must be DISABLED")
    if fixture.get("generated_at_utc") != DETERMINISTIC_CREATED_AT:
        failures.append(f"authority fixture.generated_at_utc must be {DETERMINISTIC_CREATED_AT}")
    for field, expected in {
        "owner_approved_value_tokens": OWNER_APPROVED_VALUE_TOKENS,
        "owner_decision_options": OWNER_DECISION_OPTIONS,
        "covered_domains": REQUIRED_DOMAINS,
        "covered_requirement_classes": REQUIRED_REQUIREMENT_CLASSES,
    }.items():
        values, list_failures = _list_value(fixture, field, "authority fixture")
        failures.extend(list_failures)
        missing = sorted(set(expected) - set(values))
        if missing:
            failures.append(f"authority fixture.{field} missing: {', '.join(missing)}")

    cases, list_failures = _list_value(
        fixture,
        "requirement_satisfaction_cases",
        "authority fixture",
    )
    failures.extend(list_failures)
    if len(cases) < len(REQUIRED_REQUIREMENT_CLASSES):
        failures.append("authority fixture must include at least one case per requirement class")
    seen_classes: set[str] = set()
    seen_domains: set[str] = set()
    for index, item in enumerate(cases):
        label = f"requirement_satisfaction_cases[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_fields(item, REQUIREMENT_MODEL_FIELDS, label))
        requirement_class = item.get("requirement_class")
        domain = item.get("domain")
        if isinstance(requirement_class, str):
            seen_classes.add(requirement_class)
        if isinstance(domain, str):
            seen_domains.add(domain)
        if item.get("owner_override_allowed") is not True:
            failures.append(f"{label}.owner_override_allowed must be true")
        if item.get("owner_override_applied") is not True:
            failures.append(f"{label}.owner_override_applied must be true")
        if item.get("owner_override_satisfaction_basis") not in OWNER_APPROVED_VALUE_TOKENS:
            failures.append(f"{label}.owner_override_satisfaction_basis is not a valid owner token")
        if item.get("owner_approved_value") not in OWNER_APPROVED_VALUE_TOKENS:
            failures.append(f"{label}.owner_approved_value is not a valid owner token")
        if item.get("blocks_qtt_when_owner_override_present") is not False:
            failures.append(f"{label}.blocks_qtt_when_owner_override_present must be false")
        if item.get("final_qtt_internal_status") not in FINAL_STATUS_TOKENS:
            failures.append(f"{label}.final_qtt_internal_status is not owner-satisfied")
        if item.get("externally_verified_status") != "OWNER_APPROVED_NOT_EXTERNALLY_VERIFIED":
            failures.append(f"{label}.externally_verified_status must preserve non-external verification metadata")
        if item.get("owner_approval_request_supported") is not True:
            failures.append(f"{label}.owner_approval_request_supported must be true")
        if item.get("future_dashboard_action_supported") is not True:
            failures.append(f"{label}.future_dashboard_action_supported must be true")
    missing_classes = sorted(set(REQUIRED_REQUIREMENT_CLASSES) - seen_classes)
    if missing_classes:
        failures.append(f"authority fixture missing requirement classes: {', '.join(missing_classes)}")
    missing_domains = sorted(set(REQUIRED_DOMAINS) - seen_domains)
    if missing_domains:
        failures.append(f"authority fixture missing domains: {', '.join(missing_domains)}")

    support_checks = {
        "source evidence requirements can use OWNER_GLOBAL_OVERRIDE": _has_case(
            fixture,
            "SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "final-readiness blockers can use OWNER_GLOBAL_OVERRIDE": _has_case(
            fixture,
            "FINAL_READINESS_BLOCKER_REQUIREMENT",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "validation blockers can use OWNER_GLOBAL_OVERRIDE": _has_case(
            fixture,
            "VALIDATION_GATE_REQUIREMENT",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "missing required values can use OWNER_APPROVED": _has_case(
            fixture,
            "MISSING_REQUIRED_VALUE_REQUIREMENT",
            owner_value="OWNER_APPROVED",
        ),
        "agent assignment can use AGENT_ASSIGNMENT_OWNER_APPROVED": _has_case(
            fixture,
            "ATOMICROWS_AGENT_BINDING_REQUIREMENT",
            basis="AGENT_ASSIGNMENT_OWNER_APPROVED",
        ),
        "optimizer admission can use OPTIMIZER_ADMISSION_OWNER_APPROVED": _has_case(
            fixture,
            "OPTIMIZER_ADMISSION_REQUIREMENT",
            basis="OPTIMIZER_ADMISSION_OWNER_APPROVED",
        ),
        "runtime admission can use RUNTIME_ADMISSION_OWNER_APPROVED": _has_case(
            fixture,
            "ATOMICROWS_RUNTIME_ADMISSION_REQUIREMENT",
            basis="RUNTIME_ADMISSION_OWNER_APPROVED",
        ),
        "live-use admission can use LIVE_USE_ADMISSION_OWNER_APPROVED": _has_case(
            fixture,
            "LIVE_USE_ADMISSION_REQUIREMENT",
            basis="LIVE_USE_ADMISSION_OWNER_APPROVED",
        ),
        "quantum backend can use QUANTUM_BACKEND_REQUIREMENT_OWNER_APPROVED": _has_case(
            fixture,
            "QUANTUM_BACKEND_REQUIREMENT",
            basis="QUANTUM_BACKEND_REQUIREMENT_OWNER_APPROVED",
        ),
        "replay/paper can use REPLAY_PAPER_REQUIREMENT_OWNER_APPROVED": _has_case(
            fixture,
            "REPLAY_PAPER_REQUIREMENT",
            basis="REPLAY_PAPER_REQUIREMENT_OWNER_APPROVED",
        ),
        "connector binding can use CONNECTOR_BINDING_OWNER_APPROVED": _has_case(
            fixture,
            "CONNECTOR_BINDING_REQUIREMENT",
            basis="CONNECTOR_BINDING_OWNER_APPROVED",
        ),
        "runtime resolver can use RUNTIME_RESOLVER_OWNER_APPROVED": _has_case(
            fixture,
            "RUNTIME_RESOLVER_REQUIREMENT",
            basis="RUNTIME_RESOLVER_OWNER_APPROVED",
        ),
        "generated reports can use GENERATED_REPORT_REQUIREMENT_OWNER_APPROVED": _has_case(
            fixture,
            "GENERATED_REPORT_REQUIREMENT",
            basis="GENERATED_REPORT_REQUIREMENT_OWNER_APPROVED",
        ),
        "final mode can use FINAL_MODE_BLOCKER_OWNER_APPROVED": _has_case(
            fixture,
            "FINAL_MODE_BLOCKER_REQUIREMENT",
            basis="FINAL_MODE_BLOCKER_OWNER_APPROVED",
        ),
    }
    for label, ok in sorted(support_checks.items()):
        if not ok:
            failures.append(label)

    boundary = fixture.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("authority fixture.authority_boundary must be an object")
    else:
        for field in AUTHORITY_BOUNDARY_FALSE_FIELDS + ("uses_pr_number_as_authority",):
            if boundary.get(field) is not False:
                failures.append(f"authority fixture.authority_boundary.{field} must be false")
    if fixture.get("authority_boundary_all_false") is not True:
        failures.append("authority fixture.authority_boundary_all_false must be true")
    if fixture.get("uses_pr_number_as_authority") is not False:
        failures.append("authority fixture.uses_pr_number_as_authority must be false")
    return failures


def validate_receipt_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("receipt fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("receipt fixture.execution must be DISABLED")
    receipts, list_failures = _list_value(fixture, "owner_override_receipts", "receipt fixture")
    failures.extend(list_failures)
    required_scopes = {"GLOBAL", "DOMAIN", "PARAMETER_FAMILY", "ROW", "AGENT", "REQUIREMENT", "VALUE"}
    seen_scopes = {
        receipt.get("approval_scope")
        for receipt in receipts
        if isinstance(receipt, dict)
    }
    missing_scopes = sorted(required_scopes - seen_scopes)
    if missing_scopes:
        failures.append(f"receipt fixture missing scopes: {', '.join(missing_scopes)}")
    for index, receipt in enumerate(receipts):
        label = f"owner_override_receipts[{index}]"
        if not isinstance(receipt, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_fields(receipt, RECEIPT_FIELDS, label))
        if receipt.get("authority") != "OWNER_GLOBAL_OVERRIDE":
            failures.append(f"{label}.authority must be OWNER_GLOBAL_OVERRIDE")
        if receipt.get("owner_decision") not in OWNER_DECISION_OPTIONS:
            failures.append(f"{label}.owner_decision is invalid")
        options = receipt.get("owner_decision_options")
        if not isinstance(options, list) or set(OWNER_DECISION_OPTIONS) - set(options):
            failures.append(f"{label}.owner_decision_options must include all owner options")
        if receipt.get("owner_approved_value") not in OWNER_APPROVED_VALUE_TOKENS:
            failures.append(f"{label}.owner_approved_value is invalid")
        if receipt.get("owner_override_satisfaction_basis") not in OWNER_APPROVED_VALUE_TOKENS:
            failures.append(f"{label}.owner_override_satisfaction_basis is invalid")
        if receipt.get("final_qtt_internal_status") not in FINAL_STATUS_TOKENS:
            failures.append(f"{label}.final_qtt_internal_status is invalid")
        if receipt.get("blocks_qtt_when_owner_override_present") is not False:
            failures.append(f"{label}.blocks_qtt_when_owner_override_present must be false")
        if receipt.get("created_by_owner") is not True:
            failures.append(f"{label}.created_by_owner must be true")
        if receipt.get("deterministic_created_at_utc") != DETERMINISTIC_CREATED_AT:
            failures.append(f"{label}.deterministic_created_at_utc must be deterministic")
        for field in ("future_dashboard_source_supported", "future_agent_request_source_supported"):
            if receipt.get(field) is not True:
                failures.append(f"{label}.{field} must be true")
    return failures


def validate_approval_request_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("approval request fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("approval request fixture.execution must be DISABLED")
    requests, list_failures = _list_value(
        fixture,
        "owner_approval_requests",
        "approval request fixture",
    )
    failures.extend(list_failures)
    expected_agents = {
        "SYNTHETIC_ATOMICROWS_AGENT",
        "SYNTHETIC_SOURCE_EVIDENCE_AGENT",
        "SYNTHETIC_OPTIMIZER_AGENT",
        "SYNTHETIC_RUNTIME_AGENT",
        "SYNTHETIC_LIVE_CANARY_AGENT",
    }
    seen_agents = {
        item.get("requesting_agent")
        for item in requests
        if isinstance(item, dict)
    }
    missing_agents = sorted(expected_agents - seen_agents)
    if missing_agents:
        failures.append(f"approval request fixture missing agents: {', '.join(missing_agents)}")
    for index, request in enumerate(requests):
        label = f"owner_approval_requests[{index}]"
        if not isinstance(request, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_fields(request, APPROVAL_REQUEST_FIELDS, label))
        if request.get("owner_decision_pending") is not True:
            failures.append(f"{label}.owner_decision_pending must be true")
        for field in (
            "agent_may_approve_for_owner",
            "codex_may_approve_for_owner",
            "chatgpt_may_approve_for_owner",
        ):
            if request.get(field) is not False:
                failures.append(f"{label}.{field} must be false")
        if request.get("future_dashboard_menu_supported") is not True:
            failures.append(f"{label}.future_dashboard_menu_supported must be true")
        if request.get("requested_override_basis") not in OWNER_APPROVED_VALUE_TOKENS:
            failures.append(f"{label}.requested_override_basis is invalid")
        options = request.get("requested_owner_decision_options")
        if not isinstance(options, list) or not options:
            failures.append(f"{label}.requested_owner_decision_options must be non-empty")
        elif any(option not in OWNER_DECISION_OPTIONS for option in options):
            failures.append(f"{label}.requested_owner_decision_options contains invalid option")
    return failures


def _case_count(
    fixture: dict[str, Any],
    predicate,
) -> int:
    cases = fixture.get("requirement_satisfaction_cases", [])
    if not isinstance(cases, list):
        return 0
    return sum(1 for item in cases if isinstance(item, dict) and predicate(item))


def _support_flags(fixture: dict[str, Any]) -> dict[str, bool]:
    classes = set(_records_by_class(fixture))
    return {
        "source_evidence_requirement_override_supported": _has_case(
            fixture,
            "SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "final_readiness_blocker_override_supported": _has_case(
            fixture,
            "FINAL_READINESS_BLOCKER_REQUIREMENT",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "validation_blocker_override_supported": _has_case(
            fixture,
            "VALIDATION_GATE_REQUIREMENT",
            basis="OWNER_GLOBAL_OVERRIDE",
        ),
        "compliance_marker_override_supported": (
            _has_case(fixture, "COMPLIANCE_MARKER_REQUIREMENT", basis="COMPLIANCE_MARKER_OWNER_APPROVED")
            or _has_case(fixture, "COMPLIANCE_MARKER_REQUIREMENT", owner_value="OWNER_GLOBAL_OVERRIDE")
        ),
        "atomicrows_override_supported": any(item.startswith("ATOMICROWS_") for item in classes),
        "agent_assignment_override_supported": _has_case(
            fixture,
            "ATOMICROWS_AGENT_BINDING_REQUIREMENT",
            basis="AGENT_ASSIGNMENT_OWNER_APPROVED",
        ),
        "optimizer_admission_override_supported": _has_case(
            fixture,
            "OPTIMIZER_ADMISSION_REQUIREMENT",
            basis="OPTIMIZER_ADMISSION_OWNER_APPROVED",
        ),
        "runtime_admission_override_supported": _has_case(
            fixture,
            "ATOMICROWS_RUNTIME_ADMISSION_REQUIREMENT",
            basis="RUNTIME_ADMISSION_OWNER_APPROVED",
        ),
        "live_use_admission_override_supported": _has_case(
            fixture,
            "LIVE_USE_ADMISSION_REQUIREMENT",
            basis="LIVE_USE_ADMISSION_OWNER_APPROVED",
        ),
        "quantum_backend_requirement_override_supported": _has_case(
            fixture,
            "QUANTUM_BACKEND_REQUIREMENT",
            basis="QUANTUM_BACKEND_REQUIREMENT_OWNER_APPROVED",
        ),
        "replay_paper_requirement_override_supported": _has_case(
            fixture,
            "REPLAY_PAPER_REQUIREMENT",
            basis="REPLAY_PAPER_REQUIREMENT_OWNER_APPROVED",
        ),
        "missing_required_value_override_supported": (
            _has_case(fixture, "MISSING_REQUIRED_VALUE_REQUIREMENT", basis="OWNER_GLOBAL_OVERRIDE")
            and _has_case(fixture, "MISSING_REQUIRED_VALUE_REQUIREMENT", owner_value="OWNER_APPROVED")
        ),
        "connector_binding_override_supported": _has_case(
            fixture,
            "CONNECTOR_BINDING_REQUIREMENT",
            basis="CONNECTOR_BINDING_OWNER_APPROVED",
        ),
        "runtime_resolver_override_supported": _has_case(
            fixture,
            "RUNTIME_RESOLVER_REQUIREMENT",
            basis="RUNTIME_RESOLVER_OWNER_APPROVED",
        ),
        "live_canary_override_supported": _has_case(
            fixture,
            "LIVE_CANARY_REQUIREMENT",
            basis="LIVE_CANARY_OWNER_APPROVED",
        ),
        "generated_report_override_supported": _has_case(
            fixture,
            "GENERATED_REPORT_REQUIREMENT",
            basis="GENERATED_REPORT_REQUIREMENT_OWNER_APPROVED",
        ),
        "promotion_blocker_override_supported": _has_case(
            fixture,
            "ATOMICROWS_PROMOTION_BLOCKER_REQUIREMENT",
            basis="PROMOTION_BLOCKER_OWNER_APPROVED",
        ),
        "mutation_blocker_override_supported": _has_case(
            fixture,
            "ATOMICROWS_MUTATION_BLOCKER_REQUIREMENT",
            basis="MUTATION_BLOCKER_OWNER_APPROVED",
        ),
        "final_mode_blocker_override_supported": _has_case(
            fixture,
            "FINAL_MODE_BLOCKER_REQUIREMENT",
            basis="FINAL_MODE_BLOCKER_OWNER_APPROVED",
        ),
    }


def _all_false(value: Any, fields: Iterable[str]) -> bool:
    return isinstance(value, dict) and all(value.get(field) is False for field in fields)


def build_report(
    *,
    fixture: dict[str, Any],
    receipt_fixture: dict[str, Any],
    approval_request_fixture: dict[str, Any],
    receipt_schema_present: bool,
    approval_request_schema_present: bool,
) -> dict[str, Any]:
    cases = fixture.get("requirement_satisfaction_cases", [])
    case_count = len(cases) if isinstance(cases, list) else 0
    satisfied_count = _case_count(
        fixture,
        lambda item: item.get("owner_override_applied") is True
        and item.get("final_qtt_internal_status") in FINAL_STATUS_TOKENS
        and item.get("blocks_qtt_when_owner_override_present") is False,
    )
    blocked_count = _case_count(
        fixture,
        lambda item: item.get("owner_override_applied") is True
        and item.get("blocks_qtt_when_owner_override_present") is not False,
    )
    blockers_resolved = _case_count(
        fixture,
        lambda item: item.get("owner_override_applied") is True
        and bool(item.get("absent_normal_prerequisites")),
    )
    approval_requests = approval_request_fixture.get("owner_approval_requests", [])
    if not isinstance(approval_requests, list):
        approval_requests = []
    receipts = receipt_fixture.get("owner_override_receipts", [])
    if not isinstance(receipts, list):
        receipts = []
    boundary = fixture.get("authority_boundary")
    authority_boundary_all_false = (
        fixture.get("authority_boundary_all_false") is True
        and _all_false(boundary, (*AUTHORITY_BOUNDARY_FALSE_FIELDS, "uses_pr_number_as_authority"))
        and _all_false(receipt_fixture.get("no_claim_flags"), AUTHORITY_BOUNDARY_FALSE_FIELDS)
        and _all_false(
            approval_request_fixture.get("no_claim_flags"),
            (
                *AUTHORITY_BOUNDARY_FALSE_FIELDS,
                "creates_owner_decision",
                "creates_real_override_receipt",
            ),
        )
    )
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_CREATED_AT,
        "owner_global_override_authority": fixture.get("owner_global_override_authority"),
        "owner_override_satisfies_all_qtt_internal_requirements": fixture.get(
            "owner_override_satisfies_all_qtt_internal_requirements"
        ),
        "chatgpt_authority_over_owner": fixture.get("chatgpt_authority_over_owner"),
        "codex_authority_over_owner": fixture.get("codex_authority_over_owner"),
        "qtt_agent_authority_over_owner": fixture.get("qtt_agent_authority_over_owner"),
        "validator_authority_over_owner": fixture.get("validator_authority_over_owner"),
        "generated_report_authority_over_owner": fixture.get(
            "generated_report_authority_over_owner"
        ),
        "qtt_gate_authority_over_owner": fixture.get("qtt_gate_authority_over_owner"),
        "owner_is_sole_final_internal_workflow_authority": fixture.get(
            "owner_is_sole_final_internal_workflow_authority"
        ),
        "validators_must_not_block_owner_override": fixture.get(
            "validators_must_not_block_owner_override"
        ),
        "codex_must_not_block_owner_override": fixture.get(
            "codex_must_not_block_owner_override"
        ),
        "chatgpt_must_not_block_owner_override": fixture.get(
            "chatgpt_must_not_block_owner_override"
        ),
        "qtt_agents_must_not_block_owner_override": fixture.get(
            "qtt_agents_must_not_block_owner_override"
        ),
        "generated_reports_must_not_block_owner_override": fixture.get(
            "generated_reports_must_not_block_owner_override"
        ),
        "validation_gates_must_not_block_owner_override": fixture.get(
            "validation_gates_must_not_block_owner_override"
        ),
        "owner_override_applies_to_all_qtt_domains": fixture.get(
            "owner_override_applies_to_all_qtt_domains"
        ),
        "owner_override_applies_to_all_qtt_internal_requirements": fixture.get(
            "owner_override_applies_to_all_qtt_internal_requirements"
        ),
        "owner_override_applies_to_missing_required_values": fixture.get(
            "owner_override_applies_to_missing_required_values"
        ),
        "owner_override_applies_to_source_evidence_requirements": fixture.get(
            "owner_override_applies_to_source_evidence_requirements"
        ),
        "owner_override_applies_to_final_readiness_blockers": fixture.get(
            "owner_override_applies_to_final_readiness_blockers"
        ),
        "owner_override_applies_to_validation_blockers": fixture.get(
            "owner_override_applies_to_validation_blockers"
        ),
        "covered_domains": fixture.get("covered_domains", []),
        "covered_requirement_classes": fixture.get("covered_requirement_classes", []),
        "covered_domain_count": len(fixture.get("covered_domains", [])),
        "covered_requirement_class_count": len(fixture.get("covered_requirement_classes", [])),
        "owner_approved_value_tokens": fixture.get("owner_approved_value_tokens", []),
        "owner_approved_value_token_count": len(fixture.get("owner_approved_value_tokens", [])),
        "owner_decision_options": fixture.get("owner_decision_options", []),
        "owner_decision_option_count": len(fixture.get("owner_decision_options", [])),
        "owner_override_fixture_case_count": case_count,
        "owner_override_satisfied_case_count": satisfied_count,
        "owner_override_blocked_case_count": blocked_count,
        "blockers_resolved_by_owner_override_count": blockers_resolved,
        "validators_block_owner_override_count": 0,
        "codex_blocks_owner_override_count": 0,
        "qtt_agents_block_owner_override_count": 0,
        "chatgpt_blocks_owner_override_count": 0,
        "generated_reports_block_owner_override_count": 0,
        "validation_gates_block_owner_override_count": 0,
        **_support_flags(fixture),
        "owner_override_receipt_schema_present": receipt_schema_present,
        "owner_approval_request_schema_present": approval_request_schema_present,
        "owner_override_receipt_fixture_present": bool(receipts),
        "owner_approval_request_fixture_present": bool(approval_requests),
        "future_dashboard_menu_supported": (
            fixture.get("future_dashboard_menu_supported") is True
            and all(
                request.get("future_dashboard_menu_supported") is True
                for request in approval_requests
                if isinstance(request, dict)
            )
            and all(
                receipt.get("future_dashboard_source_supported") is True
                for receipt in receipts
                if isinstance(receipt, dict)
            )
        ),
        "future_agent_approval_request_supported": (
            fixture.get("future_agent_approval_request_supported") is True
            and bool(approval_requests)
            and all(
                receipt.get("future_agent_request_source_supported") is True
                for receipt in receipts
                if isinstance(receipt, dict)
            )
        ),
        "agent_may_approve_for_owner": any(
            request.get("agent_may_approve_for_owner") is True
            for request in approval_requests
            if isinstance(request, dict)
        ),
        "codex_may_approve_for_owner": any(
            request.get("codex_may_approve_for_owner") is True
            for request in approval_requests
            if isinstance(request, dict)
        ),
        "chatgpt_may_approve_for_owner": any(
            request.get("chatgpt_may_approve_for_owner") is True
            for request in approval_requests
            if isinstance(request, dict)
        ),
        "uses_pr_number_as_authority": fixture.get("uses_pr_number_as_authority") is True,
        "authority_boundary_all_false": authority_boundary_all_false,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_true = {
        "deterministic_output",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "owner_is_sole_final_internal_workflow_authority",
        "validators_must_not_block_owner_override",
        "codex_must_not_block_owner_override",
        "chatgpt_must_not_block_owner_override",
        "qtt_agents_must_not_block_owner_override",
        "generated_reports_must_not_block_owner_override",
        "validation_gates_must_not_block_owner_override",
        "owner_override_applies_to_all_qtt_domains",
        "owner_override_applies_to_all_qtt_internal_requirements",
        "owner_override_applies_to_missing_required_values",
        "owner_override_applies_to_source_evidence_requirements",
        "owner_override_applies_to_final_readiness_blockers",
        "owner_override_applies_to_validation_blockers",
        "source_evidence_requirement_override_supported",
        "final_readiness_blocker_override_supported",
        "validation_blocker_override_supported",
        "compliance_marker_override_supported",
        "atomicrows_override_supported",
        "agent_assignment_override_supported",
        "optimizer_admission_override_supported",
        "runtime_admission_override_supported",
        "live_use_admission_override_supported",
        "quantum_backend_requirement_override_supported",
        "replay_paper_requirement_override_supported",
        "missing_required_value_override_supported",
        "connector_binding_override_supported",
        "runtime_resolver_override_supported",
        "live_canary_override_supported",
        "generated_report_override_supported",
        "promotion_blocker_override_supported",
        "mutation_blocker_override_supported",
        "final_mode_blocker_override_supported",
        "owner_override_receipt_schema_present",
        "owner_approval_request_schema_present",
        "owner_override_receipt_fixture_present",
        "owner_approval_request_fixture_present",
        "future_dashboard_menu_supported",
        "future_agent_approval_request_supported",
        "authority_boundary_all_false",
    }
    expected_false = {
        "chatgpt_authority_over_owner",
        "codex_authority_over_owner",
        "qtt_agent_authority_over_owner",
        "validator_authority_over_owner",
        "generated_report_authority_over_owner",
        "qtt_gate_authority_over_owner",
        "agent_may_approve_for_owner",
        "codex_may_approve_for_owner",
        "chatgpt_may_approve_for_owner",
        "uses_pr_number_as_authority",
    }
    for field in sorted(expected_true):
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    for field in sorted(expected_false):
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    for field in (
        "owner_override_blocked_case_count",
        "validators_block_owner_override_count",
        "codex_blocks_owner_override_count",
        "qtt_agents_block_owner_override_count",
        "chatgpt_blocks_owner_override_count",
        "generated_reports_block_owner_override_count",
        "validation_gates_block_owner_override_count",
    ):
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    if report.get("generated_at_utc") != DETERMINISTIC_CREATED_AT:
        failures.append(f"report.generated_at_utc must be {DETERMINISTIC_CREATED_AT}")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("blockers_resolved_by_owner_override_count", 0) < 15:
        failures.append("report.blockers_resolved_by_owner_override_count must be >= 15")
    if report.get("covered_domain_count", 0) < len(REQUIRED_DOMAINS):
        failures.append("report.covered_domain_count is too low")
    if report.get("covered_requirement_class_count", 0) < len(REQUIRED_REQUIREMENT_CLASSES):
        failures.append("report.covered_requirement_class_count is too low")
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    global_schema_path: pathlib.Path = DEFAULT_GLOBAL_SCHEMA,
    receipt_schema_path: pathlib.Path = DEFAULT_RECEIPT_SCHEMA,
    approval_request_schema_path: pathlib.Path = DEFAULT_APPROVAL_REQUEST_SCHEMA,
    policy_path: pathlib.Path = DEFAULT_POLICY,
    authority_fixture_path: pathlib.Path = DEFAULT_AUTHORITY_FIXTURE,
    receipt_fixture_path: pathlib.Path = DEFAULT_RECEIPT_FIXTURE,
    approval_request_fixture_path: pathlib.Path = DEFAULT_APPROVAL_REQUEST_FIXTURE,
    report_path: pathlib.Path | None = None,
) -> tuple[list[str], dict[str, Any] | None]:
    del repo_root
    failures: list[str] = []
    global_schema, global_schema_failures = _load_json(global_schema_path)
    receipt_schema, receipt_schema_failures = _load_json(receipt_schema_path)
    approval_schema, approval_schema_failures = _load_json(approval_request_schema_path)
    authority_fixture, authority_fixture_failures = _load_json(authority_fixture_path)
    receipt_fixture, receipt_fixture_failures = _load_json(receipt_fixture_path)
    approval_fixture, approval_fixture_failures = _load_json(approval_request_fixture_path)
    policy, policy_failures = _parse_policy_yaml(policy_path)
    failures.extend(global_schema_failures)
    failures.extend(receipt_schema_failures)
    failures.extend(approval_schema_failures)
    failures.extend(authority_fixture_failures)
    failures.extend(receipt_fixture_failures)
    failures.extend(approval_fixture_failures)
    failures.extend(policy_failures)

    if global_schema is not None:
        failures.extend(validate_global_schema(global_schema))
    if receipt_schema is not None:
        failures.extend(validate_receipt_schema(receipt_schema))
    if approval_schema is not None:
        failures.extend(validate_approval_request_schema(approval_schema))
    if policy is not None:
        failures.extend(validate_policy(policy))
    if authority_fixture is not None:
        failures.extend(validate_authority_fixture(authority_fixture))
    if receipt_fixture is not None:
        failures.extend(validate_receipt_fixture(receipt_fixture))
    if approval_fixture is not None:
        failures.extend(validate_approval_request_fixture(approval_fixture))

    report: dict[str, Any] | None = None
    if (
        authority_fixture is not None
        and receipt_fixture is not None
        and approval_fixture is not None
    ):
        report = build_report(
            fixture=authority_fixture,
            receipt_fixture=receipt_fixture,
            approval_request_fixture=approval_fixture,
            receipt_schema_present=receipt_schema_path.exists(),
            approval_request_schema_present=approval_request_schema_path.exists(),
        )
        failures.extend(validate_report(report))

    if report_path is not None and report_path.exists() and report is not None:
        existing_report, report_failures = _load_json(report_path)
        failures.extend(report_failures)
        if existing_report is not None and existing_report != report:
            failures.append(f"generated report is not deterministic/current: {report_path}")
    return failures, report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev"], default="dev")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--global-schema", default=str(DEFAULT_GLOBAL_SCHEMA))
    parser.add_argument("--receipt-schema", default=str(DEFAULT_RECEIPT_SCHEMA))
    parser.add_argument("--approval-request-schema", default=str(DEFAULT_APPROVAL_REQUEST_SCHEMA))
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--fixture", default=str(DEFAULT_AUTHORITY_FIXTURE))
    parser.add_argument("--receipt-fixture", default=str(DEFAULT_RECEIPT_FIXTURE))
    parser.add_argument("--approval-request-fixture", default=str(DEFAULT_APPROVAL_REQUEST_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = pathlib.Path(args.repo_root)
    out_path = repo_root / pathlib.Path(args.out)
    failures, report = validate_static_surface(
        repo_root=repo_root,
        global_schema_path=pathlib.Path(args.global_schema),
        receipt_schema_path=pathlib.Path(args.receipt_schema),
        approval_request_schema_path=pathlib.Path(args.approval_request_schema),
        policy_path=pathlib.Path(args.policy),
        authority_fixture_path=pathlib.Path(args.fixture),
        receipt_fixture_path=pathlib.Path(args.receipt_fixture),
        approval_request_fixture_path=pathlib.Path(args.approval_request_fixture),
    )
    if report is not None:
        _write_json(out_path, report)
        report_failures, _ = validate_static_surface(
            repo_root=repo_root,
            global_schema_path=pathlib.Path(args.global_schema),
            receipt_schema_path=pathlib.Path(args.receipt_schema),
            approval_request_schema_path=pathlib.Path(args.approval_request_schema),
            policy_path=pathlib.Path(args.policy),
            authority_fixture_path=pathlib.Path(args.fixture),
            receipt_fixture_path=pathlib.Path(args.receipt_fixture),
            approval_request_fixture_path=pathlib.Path(args.approval_request_fixture),
            report_path=out_path,
        )
        failures = report_failures
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
