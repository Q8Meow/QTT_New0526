#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

SUCCESS_MARKER = "ATOMICROWS_CANONICAL_ROW_SPECIFICATION_STATIC_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_CANONICAL_ROW_SPECIFICATION_STATIC_VALIDATION_FAILED"

BLOCKED_STATUS = "BLOCKED_PENDING_ATOMICROWS_CANONICAL_ROW_SPECIFICATION_AUTHORITY"
REQUIREMENT_ONLY_STATUS = "REQUIREMENT_ONLY_NOT_ATOMICROWS_AUTHORITY"
UNBOUND_ROW_COUNT = "UNBOUND_NO_BUNDLE_AUTHORITY"

CANONICAL_BUNDLE_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "audit_status",
    "expected_canonical_paths",
    "atomicrows_authority_state",
    "canonical_row_specification_requirements",
    "canonical_row_specification_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_PR29_ATOMICROWS_CANONICAL_ROW_SPECIFICATION_REQUIRED_FIXTURE"
    ),
    "fixture_version": (
        "PR29_ATOMICROWS_CANONICAL_ROW_SPECIFICATION_REQUIRED_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
    ),
    "schema_authority_class": "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_AUTHORITY",
    "surface_kind": "ATOMICROWS_CANONICAL_ROW_SPECIFICATION_AUDIT_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "audit_status": BLOCKED_STATUS,
}

EXPECTED_PATH_FIELDS = {
    "canonical_bundle_path",
    "canonical_bundle_sha_path",
}

EXPECTED_PATH_CONSTS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
}

AUTHORITY_STATE_FIELDS = {
    "canonical_bundle_present",
    "canonical_bundle_sha_present",
    "bundle_authority_present",
    "hash_authority_present",
    "row_specification_authority_present",
    "row_creation_authority_present",
    "completion_authority_present",
    "blocker_reduction_present",
    "runtime_authority_present",
    "source_authority_present",
    "connector_authority_present",
    "private_state_authority_present",
    "order_authority_present",
    "sha_freeze_authority_present",
    "profit_authority_present",
    "audit_status",
    "claimed_atomicrows_row_count",
}

AUTHORITY_STATE_CONST_EXPECTATIONS = {
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "bundle_authority_present": False,
    "hash_authority_present": False,
    "row_specification_authority_present": False,
    "row_creation_authority_present": False,
    "completion_authority_present": False,
    "blocker_reduction_present": False,
    "runtime_authority_present": False,
    "source_authority_present": False,
    "connector_authority_present": False,
    "private_state_authority_present": False,
    "order_authority_present": False,
    "sha_freeze_authority_present": False,
    "profit_authority_present": False,
    "audit_status": BLOCKED_STATUS,
    "claimed_atomicrows_row_count": UNBOUND_ROW_COUNT,
}

REQUIREMENT_FIELDS = {
    "requirement_id",
    "current_status",
    "required_before_future_bundle_creation",
    "required_precondition",
    "current_pr_assertion",
    "blocked_until",
}

EXPECTED_REQUIREMENTS = {
    "CANONICAL_ROW_ID_FIELD_FORMAT_REQUIREMENT": {
        "requirement_id": "CANONICAL_ROW_ID_FIELD_FORMAT_REQUIREMENT",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must declare a canonical row id "
            "field and a strict format requirement before any row records are "
            "accepted."
        ),
        "current_pr_assertion": (
            "Current PR declares only this requirement and creates no row ids or rows."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "REQUIRED_ROW_FIELDS_DECLARATION": {
        "requirement_id": "REQUIRED_ROW_FIELDS_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the "
            "complete required row field set before any row records are accepted."
        ),
        "current_pr_assertion": (
            "Current PR requires the declaration and creates no required-field "
            "authority."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "ALLOWED_ROW_AUTHORITY_CLASSES_DECLARATION": {
        "requirement_id": "ALLOWED_ROW_AUTHORITY_CLASSES_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare every "
            "allowed row authority class before rows are accepted."
        ),
        "current_pr_assertion": (
            "Current PR requires allowed authority class declaration but grants no "
            "row authority class."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "ROW_ORDERING_RULE_DECLARATION": {
        "requirement_id": "ROW_ORDERING_RULE_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the row "
            "ordering rule used to serialize the canonical JSONL bundle."
        ),
        "current_pr_assertion": (
            "Current PR requires the ordering rule and creates no ordered rows."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "CANONICAL_JSON_KEY_ORDERING_RULE_DECLARATION": {
        "requirement_id": "CANONICAL_JSON_KEY_ORDERING_RULE_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the "
            "canonical JSON object key ordering rule."
        ),
        "current_pr_assertion": (
            "Current PR requires the key ordering rule and creates no JSONL rows."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "UTF8_ENCODING_RULE_DECLARATION": {
        "requirement_id": "UTF8_ENCODING_RULE_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the "
            "UTF-8 byte encoding rule."
        ),
        "current_pr_assertion": (
            "Current PR requires the UTF-8 rule and writes no bundle bytes."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "NEWLINE_POLICY_DECLARATION": {
        "requirement_id": "NEWLINE_POLICY_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the "
            "newline policy for canonical JSONL serialization."
        ),
        "current_pr_assertion": (
            "Current PR requires the newline policy and writes no bundle lines."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "JSONL_ONE_OBJECT_PER_LINE_RULE_DECLARATION": {
        "requirement_id": "JSONL_ONE_OBJECT_PER_LINE_RULE_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly declare the "
            "JSONL one-object-per-line rule."
        ),
        "current_pr_assertion": (
            "Current PR requires the JSONL rule and creates no JSONL content."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "TIMESTAMP_OS_METADATA_EXCLUSION_DECLARATION": {
        "requirement_id": "TIMESTAMP_OS_METADATA_EXCLUSION_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly exclude "
            "timestamp and OS metadata unless later explicit authority allows them."
        ),
        "current_pr_assertion": (
            "Current PR requires metadata exclusion and grants no metadata authority."
        ),
        "blocked_until": "Future explicit metadata authority, if any, outside this audit.",
    },
    "SOURCE_AUTHORITY_REQUIREMENT_PER_ROW_DECLARATION": {
        "requirement_id": "SOURCE_AUTHORITY_REQUIREMENT_PER_ROW_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly require source "
            "authority for each row before any row is accepted."
        ),
        "current_pr_assertion": (
            "Current PR requires per-row source authority but accepts no source facts."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "NO_ROW_INVENTION_RULE_DECLARATION": {
        "requirement_id": "NO_ROW_INVENTION_RULE_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly prohibit row "
            "invention, including invented rows used to reach 4,183 rows."
        ),
        "current_pr_assertion": (
            "Current PR preserves the no-row-invention blocker and creates no rows."
        ),
        "blocked_until": "Future source-backed row specification authority.",
    },
    "NO_COMPLETION_CLAIM_WITHOUT_BUNDLE_HASH_DECLARATION": {
        "requirement_id": "NO_COMPLETION_CLAIM_WITHOUT_BUNDLE_HASH_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future authorized AtomicRows bundle must explicitly prohibit any "
            "completion claim without the actual canonical bundle and hash."
        ),
        "current_pr_assertion": (
            "Current PR permits no completion claim because bundle/hash are absent."
        ),
        "blocked_until": "Actual canonical bundle/hash and explicit completion gates.",
    },
    "CANONICAL_BUNDLE_PATH_DECLARATION": {
        "requirement_id": "CANONICAL_BUNDLE_PATH_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "The future authorized AtomicRows bundle path must remain "
            "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl."
        ),
        "current_pr_assertion": (
            "Current PR validates the path requirement and creates no bundle file."
        ),
        "blocked_until": "Future explicit owner bundle creation command.",
    },
    "CANONICAL_BUNDLE_SHA_PATH_DECLARATION": {
        "requirement_id": "CANONICAL_BUNDLE_SHA_PATH_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "The future authorized AtomicRows bundle hash path must remain "
            "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256."
        ),
        "current_pr_assertion": (
            "Current PR validates the hash path requirement and creates no hash file."
        ),
        "blocked_until": "Future explicit owner hash creation command.",
    },
    "BOOTSTRAP_ABSENCE_REMAINS_VALID_DECLARATION": {
        "requirement_id": "BOOTSTRAP_ABSENCE_REMAINS_VALID_DECLARATION",
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "AtomicRows bundle/hash absence must remain valid in bootstrap blocked "
            "mode and must not be treated as completion."
        ),
        "current_pr_assertion": (
            "Current PR preserves blocked bootstrap absence and no completion claim."
        ),
        "blocked_until": "Future explicit owner bundle/hash creation command.",
    },
    "AUDIT_HAS_NO_BUNDLE_HASH_ROW_SHA_UNBLOCK_AUTHORITY_DECLARATION": {
        "requirement_id": (
            "AUDIT_HAS_NO_BUNDLE_HASH_ROW_SHA_UNBLOCK_AUTHORITY_DECLARATION"
        ),
        "current_status": REQUIREMENT_ONLY_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "This audit must explicitly create no bundle, no hash, no rows, no SHA, "
            "and no AtomicRows unblock authority."
        ),
        "current_pr_assertion": (
            "Current PR is non-mutating and grants no bundle/hash/row/SHA/unblock "
            "authority."
        ),
        "blocked_until": "Separate future explicit owner authorization.",
    },
}

CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS = {
    "non_mutating_static_audit": True,
    "deterministic_static_fixture_only": True,
    "requirement_audit_only": True,
    "canonical_row_specification_requirements_only": True,
    "canonical_row_id_format_requirement_declared": True,
    "required_row_fields_declaration_required": True,
    "allowed_row_authority_classes_declaration_required": True,
    "row_ordering_rule_declaration_required": True,
    "canonical_json_key_ordering_rule_declaration_required": True,
    "utf8_encoding_rule_declaration_required": True,
    "newline_policy_declaration_required": True,
    "jsonl_one_object_per_line_rule_declaration_required": True,
    "timestamp_os_metadata_exclusion_required_unless_explicit_authority": True,
    "source_authority_requirement_per_row_required": True,
    "no_row_invention_required": True,
    "no_completion_claim_without_bundle_hash_required": True,
    "canonical_bundle_path_fixed": True,
    "canonical_bundle_sha_path_fixed": True,
    "bundle_absence_bootstrap_allowed": True,
    "current_state_blocked": True,
    "validates_absence_of_bundle_and_hash": True,
    "writes_output_files_by_default": False,
    "creates_bundle_hash_or_rows": False,
    "treats_audit_as_bundle_hash_authority": False,
    "permits_timestamp_or_os_metadata_without_authority": False,
    "permits_row_invention": False,
    "permits_completion_claim_without_bundle_hash": False,
    "completion_claim_allowed": False,
    "row_count_completion_claim_allowed": False,
    "blocker_reduction_allowed": False,
    "runtime_use_allowed": False,
    "live_use_allowed": False,
    "source_retrieval_allowed": False,
    "source_acceptance_allowed": False,
    "source_fact_acceptance_allowed": False,
    "connector_binding_allowed": False,
    "private_state_fetch_allowed": False,
    "order_execution_allowed": False,
    "sha_computation_allowed": False,
    "sha_freeze_allowed": False,
    "profit_claim_allowed": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_row_creation_enabled",
    "actual_row_record_creation_enabled",
    "row_invention_enabled",
    "synthetic_row_completion_enabled",
    "generated_authoritative_row_bundle_enabled",
    "completion_claim_enabled",
    "row_count_completion_claim_enabled",
    "blocker_reduction_enabled",
    "requirement_satisfaction_enabled",
    "audit_as_bundle_authority_enabled",
    "audit_as_hash_authority_enabled",
    "audit_as_unblock_authority_enabled",
    "source_authority_creation_enabled",
    "timestamp_metadata_permission_enabled",
    "os_metadata_permission_enabled",
    "runtime_enabled",
    "runtime_execution_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "live_enabled",
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "private_state_fetch_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "sha_freeze_enabled",
    "freeze_authority_enabled",
    "profit_claim_enabled",
}

NO_CLAIM_FLAGS = {
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_atomicrows_rows",
    "contains_atomicrows_row_records",
    "contains_actual_row_records",
    "contains_synthetic_completed_rows",
    "contains_generated_authoritative_row_bundle",
    "claims_atomicrows_completion",
    "claims_4183_row_completion",
    "claims_atomicrows_row_count_completion",
    "claims_blocker_reduction",
    "claims_requirement_satisfaction",
    "claims_bundle_authority",
    "claims_hash_authority",
    "claims_row_specification_authority",
    "claims_source_authority",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "creates_atomicrows_rows",
    "creates_actual_row_records",
    "computes_atomicrows_sha",
    "creates_sha_freeze_authority",
    "creates_freeze_authority",
    "creates_runtime_authority",
    "creates_runtime_trading_authority",
    "creates_live_authority",
    "creates_source_retrieval",
    "creates_source_authority",
    "accepts_source_facts",
    "accepts_external_facts",
    "treats_owner_policy_as_external_fact_authority",
    "binds_connector",
    "binds_connector_semantics",
    "fetches_private_state",
    "creates_runtime_resolver_snapshot",
    "executes_replay",
    "executes_paper",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "creates_profit_evidence",
    "creates_profit_claim",
    "permits_timestamps_without_authority",
    "permits_os_metadata_without_authority",
    "weakens_no_row_invention",
    "treats_audit_as_actual_bundle_authority",
    "treats_audit_as_actual_hash_authority",
    "treats_audit_as_unblock_authority",
}

EXPECTED_SCHEMA_DEFS = {
    "expected_canonical_paths",
    "authority_state",
    "requirement_entry",
    "canonical_row_specification_requirements",
    "canonical_row_specification_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
}

FORBIDDEN_ROW_RECORD_KEYS = {
    "row",
    "rows",
    "row_record",
    "row_records",
    "atomic_row",
    "atomic_rows",
    "atomicrows_row",
    "atomicrows_rows",
    "atomicrows_row_record",
    "atomicrows_row_records",
    "bundle_row",
    "bundle_rows",
    "jsonl_row",
    "jsonl_rows",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "http",
    "https",
    "kalshi",
    "polymarket",
    "forecastx",
    "forecastex",
    "ibkr",
    "interactivebrokers",
    "secret_key",
    "client_secret",
    "sk_live",
    "pk_live",
    "bearer ",
    "password",
    "account_id",
    "owner_uploaded_private_doc_locator",
    "-----begin",
}


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


def _properties(definition: dict[str, Any]) -> dict[str, Any]:
    properties = definition.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _const_value(definition: dict[str, Any], property_name: str) -> Any:
    prop = _properties(definition).get(property_name, {})
    return prop.get("const") if isinstance(prop, dict) else None


def _require_exact_fields(value: dict[str, Any], fields: set[str], label: str) -> list[str]:
    failures: list[str] = []
    missing = sorted(fields - set(value))
    unexpected = sorted(set(value) - fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _validate_schema_object_contract(
    definition: dict[str, Any],
    *,
    expected_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    if definition.get("type") != "object":
        failures.append(f"{label}.type must be object")
    if definition.get("additionalProperties") is not False:
        failures.append(f"{label}.additionalProperties must be false")

    properties = definition.get("properties")
    if not isinstance(properties, dict):
        failures.append(f"{label}.properties must be an object")
    else:
        failures.extend(_require_exact_fields(properties, expected_fields, f"{label}.properties"))

    required = definition.get("required")
    if not isinstance(required, list):
        failures.append(f"{label}.required must be a list")
    else:
        required_fields = set(required)
        missing_required = sorted(expected_fields - required_fields)
        unexpected_required = sorted(required_fields - expected_fields)
        if missing_required:
            failures.append(f"{label} missing required fields: {', '.join(missing_required)}")
        if unexpected_required:
            failures.append(f"{label} has unexpected required fields: {', '.join(unexpected_required)}")
        if len(required) != len(required_fields):
            failures.append(f"{label}.required must not contain duplicate fields")
    return failures


def _validate_boolean_const_schema(
    definition: dict[str, Any],
    *,
    expected: dict[str, bool],
    label: str,
) -> list[str]:
    failures = _validate_schema_object_contract(
        definition,
        expected_fields=set(expected),
        label=label,
    )
    for field, expected_value in sorted(expected.items()):
        if _const_value(definition, field) is not expected_value:
            failures.append(f"{label}.{field} must be const {expected_value}")
    return failures


def _validate_const_schema(
    definition: dict[str, Any],
    *,
    expected: dict[str, Any],
    label: str,
) -> list[str]:
    failures = _validate_schema_object_contract(
        definition,
        expected_fields=set(expected),
        label=label,
    )
    for field, expected_value in sorted(expected.items()):
        if _const_value(definition, field) != expected_value:
            failures.append(f"{label}.{field} must be const {expected_value}")
    return failures


def _mapping(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _validate_bool_map(
    value: dict[str, Any],
    expected: dict[str, bool] | set[str],
    label: str,
) -> list[str]:
    expected_values = (
        {field: False for field in expected}
        if isinstance(expected, set)
        else dict(expected)
    )
    failures = _require_exact_fields(value, set(expected_values), label)
    for field, expected_value in sorted(expected_values.items()):
        if field in value and value[field] is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def _walk(value: Any, path: str = "fixture"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _canonical_path(root: pathlib.Path, rel_path: pathlib.PurePosixPath) -> pathlib.Path:
    return root / pathlib.Path(*rel_path.parts)


def _actual_presence(repo_root: pathlib.Path) -> tuple[bool, bool]:
    root = repo_root.resolve()
    bundle_path = _canonical_path(root, CANONICAL_BUNDLE_RELATIVE_PATH)
    sha_path = _canonical_path(root, CANONICAL_BUNDLE_SHA_RELATIVE_PATH)
    return bundle_path.exists(), sha_path.exists()


def _validate_requirement_categories_schema(definition: dict[str, Any]) -> list[str]:
    failures = _validate_schema_object_contract(
        definition,
        expected_fields=set(EXPECTED_REQUIREMENTS),
        label="schema.$defs.canonical_row_specification_requirements",
    )
    properties = _properties(definition)
    for field in sorted(EXPECTED_REQUIREMENTS):
        prop = properties.get(field)
        if not isinstance(prop, dict) or prop.get("$ref") != "#/$defs/requirement_entry":
            failures.append(
                "schema.$defs.canonical_row_specification_requirements."
                f"{field} must reference #/$defs/requirement_entry"
            )
    return failures


def _validate_schema(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _validate_schema_object_contract(
            schema,
            expected_fields=ROOT_FIELDS,
            label="schema",
        )
    )

    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"schema.properties.{field} must be const {expected}")

    properties = _properties(schema)
    expected_refs = {
        "expected_canonical_paths": "#/$defs/expected_canonical_paths",
        "atomicrows_authority_state": "#/$defs/authority_state",
        "canonical_row_specification_requirements": (
            "#/$defs/canonical_row_specification_requirements"
        ),
        "canonical_row_specification_scope_flags": (
            "#/$defs/canonical_row_specification_scope_flags"
        ),
        "forbidden_action_flags": "#/$defs/forbidden_action_flags",
        "no_claim_flags": "#/$defs/no_claim_flags",
    }
    for field, expected_ref in sorted(expected_refs.items()):
        prop = properties.get(field, {})
        if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
            failures.append(f"schema.properties.{field} must reference {expected_ref}")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, EXPECTED_SCHEMA_DEFS, "schema.$defs"))

    path_def = defs.get("expected_canonical_paths")
    if isinstance(path_def, dict):
        failures.extend(
            _validate_const_schema(
                path_def,
                expected=EXPECTED_PATH_CONSTS,
                label="schema.$defs.expected_canonical_paths",
            )
        )
    else:
        failures.append("schema.$defs.expected_canonical_paths must be an object")

    authority_state = defs.get("authority_state")
    if isinstance(authority_state, dict):
        failures.extend(
            _validate_const_schema(
                authority_state,
                expected=AUTHORITY_STATE_CONST_EXPECTATIONS,
                label="schema.$defs.authority_state",
            )
        )
    else:
        failures.append("schema.$defs.authority_state must be an object")

    requirement_entry = defs.get("requirement_entry")
    if isinstance(requirement_entry, dict):
        failures.extend(
            _validate_schema_object_contract(
                requirement_entry,
                expected_fields=REQUIREMENT_FIELDS,
                label="schema.$defs.requirement_entry",
            )
        )
    else:
        failures.append("schema.$defs.requirement_entry must be an object")

    requirements = defs.get("canonical_row_specification_requirements")
    if isinstance(requirements, dict):
        failures.extend(_validate_requirement_categories_schema(requirements))
    else:
        failures.append(
            "schema.$defs.canonical_row_specification_requirements must be an object"
        )

    scope_flags = defs.get("canonical_row_specification_scope_flags")
    if isinstance(scope_flags, dict):
        failures.extend(
            _validate_boolean_const_schema(
                scope_flags,
                expected=CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS,
                label="schema.$defs.canonical_row_specification_scope_flags",
            )
        )
    else:
        failures.append(
            "schema.$defs.canonical_row_specification_scope_flags must be an object"
        )

    forbidden_actions = defs.get("forbidden_action_flags")
    if isinstance(forbidden_actions, dict):
        failures.extend(
            _validate_boolean_const_schema(
                forbidden_actions,
                expected={field: False for field in FORBIDDEN_ACTION_FLAGS},
                label="schema.$defs.forbidden_action_flags",
            )
        )
    else:
        failures.append("schema.$defs.forbidden_action_flags must be an object")

    no_claim_flags = defs.get("no_claim_flags")
    if isinstance(no_claim_flags, dict):
        failures.extend(
            _validate_boolean_const_schema(
                no_claim_flags,
                expected={field: False for field in NO_CLAIM_FLAGS},
                label="schema.$defs.no_claim_flags",
            )
        )
    else:
        failures.append("schema.$defs.no_claim_flags must be an object")

    return failures


def _validate_expected_paths(paths: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        paths,
        EXPECTED_PATH_FIELDS,
        "expected_canonical_paths",
    )
    for field, expected in sorted(EXPECTED_PATH_CONSTS.items()):
        if paths.get(field) != expected:
            failures.append(f"expected_canonical_paths.{field} must be {expected}")
    return failures


def _validate_authority_state(
    state: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(state, AUTHORITY_STATE_FIELDS, "atomicrows_authority_state")
    for field, expected in sorted(AUTHORITY_STATE_CONST_EXPECTATIONS.items()):
        if state.get(field) != expected:
            failures.append(f"atomicrows_authority_state.{field} must be {expected}")

    bundle_present, sha_present = _actual_presence(repo_root)
    if state.get("canonical_bundle_present") is not bundle_present:
        failures.append(
            "atomicrows_authority_state.canonical_bundle_present must match "
            f"filesystem presence {bundle_present}"
        )
    if state.get("canonical_bundle_sha_present") is not sha_present:
        failures.append(
            "atomicrows_authority_state.canonical_bundle_sha_present must match "
            f"filesystem presence {sha_present}"
        )
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="canonical row specification validation",
        )
    )

    if state.get("audit_status") != BLOCKED_STATUS:
        failures.append(
            "atomicrows_authority_state.audit_status must be "
            f"{BLOCKED_STATUS}"
        )
    for field in sorted(AUTHORITY_STATE_FIELDS - {"audit_status", "claimed_atomicrows_row_count"}):
        if state.get(field) is not False:
            failures.append(f"atomicrows_authority_state.{field} must be false")
    if state.get("claimed_atomicrows_row_count") != UNBOUND_ROW_COUNT:
        failures.append(
            "atomicrows_authority_state.claimed_atomicrows_row_count must remain "
            f"{UNBOUND_ROW_COUNT}"
        )
    return failures


def _validate_requirement_categories(categories: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        categories,
        set(EXPECTED_REQUIREMENTS),
        "canonical_row_specification_requirements",
    )
    for requirement_id, expected in sorted(EXPECTED_REQUIREMENTS.items()):
        entry = categories.get(requirement_id)
        if not isinstance(entry, dict):
            failures.append(
                f"canonical_row_specification_requirements.{requirement_id} "
                "must be an object"
            )
            continue
        failures.extend(
            _require_exact_fields(
                entry,
                REQUIREMENT_FIELDS,
                f"canonical_row_specification_requirements.{requirement_id}",
            )
        )
        for field, expected_value in sorted(expected.items()):
            if entry.get(field) != expected_value:
                failures.append(
                    f"canonical_row_specification_requirements.{requirement_id}."
                    f"{field} must be {expected_value}"
                )
        if entry.get("current_status") != REQUIREMENT_ONLY_STATUS:
            failures.append(
                f"canonical_row_specification_requirements.{requirement_id}."
                f"current_status must be {REQUIREMENT_ONLY_STATUS}"
            )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        set(FORBIDDEN_ACTION_FLAGS)
        | set(NO_CLAIM_FLAGS)
        | {
            field
            for field, expected in CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in AUTHORITY_STATE_CONST_EXPECTATIONS.items()
            if expected is False
        }
    )
    must_be_true = {
        field
        for field, expected in CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS.items()
        if expected is True
    }

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain actual AtomicRows row records")
        if key == "audit_status" and item != BLOCKED_STATUS:
            failures.append(f"{path} must be {BLOCKED_STATUS}")
        if key == "claimed_atomicrows_row_count" and item != UNBOUND_ROW_COUNT:
            failures.append(f"{path} must be {UNBOUND_ROW_COUNT}")
        if key == "current_status" and item != REQUIREMENT_ONLY_STATUS:
            failures.append(f"{path} must be {REQUIREMENT_ONLY_STATUS}")
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric AtomicRows row claims")
        if isinstance(item, str):
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_atomicrows_canonical_row_specification_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "atomicrows canonical row specification fixture",
    )
    for field, value in ROOT_CONST_EXPECTATIONS.items():
        if fixture.get(field) != value:
            failures.append(
                "atomicrows canonical row specification fixture."
                f"{field} must be {value}"
            )

    expected_paths, path_failures = _mapping(
        fixture,
        "expected_canonical_paths",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(path_failures)
    if expected_paths is not None:
        failures.extend(_validate_expected_paths(expected_paths))

    authority_state, authority_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(authority_failures)
    if authority_state is not None:
        failures.extend(_validate_authority_state(authority_state, repo_root=repo_root))

    requirements, requirement_failures = _mapping(
        fixture,
        "canonical_row_specification_requirements",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(requirement_failures)
    if requirements is not None:
        failures.extend(_validate_requirement_categories(requirements))

    scope_flags, scope_failures = _mapping(
        fixture,
        "canonical_row_specification_scope_flags",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_bool_map(
                scope_flags,
                CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS,
                "canonical_row_specification_scope_flags",
            )
        )

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(action_failures)
    if forbidden_actions is not None:
        failures.extend(
            _validate_bool_map(
                forbidden_actions,
                FORBIDDEN_ACTION_FLAGS,
                "forbidden_action_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping(
        fixture,
        "no_claim_flags",
        "atomicrows canonical row specification fixture",
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_bool_map(
                no_claim_flags,
                NO_CLAIM_FLAGS,
                "no_claim_flags",
            )
        )

    hook_ids = fixture.get("validation_hook_ids")
    if not isinstance(hook_ids, list) or hook_ids != [
        "ATOMICROWS_CANONICAL_ROW_SPECIFICATION_STATIC_NON_MUTATING_AUDIT"
    ]:
        failures.append(
            "atomicrows canonical row specification fixture.validation_hook_ids "
            "must contain only "
            "ATOMICROWS_CANONICAL_ROW_SPECIFICATION_STATIC_NON_MUTATING_AUDIT"
        )

    failures.extend(_validate_no_forbidden_claims(fixture))
    return failures


def validate_static_surface(
    *,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    schema, schema_failures = _load_json(schema_path)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)
    if schema is not None:
        failures.extend(_validate_schema(schema))
    if fixture is not None:
        failures.extend(
            validate_atomicrows_canonical_row_specification_fixture(
                fixture,
                repo_root=repo_root,
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        repo_root=pathlib.Path(args.repo_root),
    )
    if failures:
        raise SystemExit(FAILURE_MARKER + "\n- " + "\n- ".join(failures))
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
