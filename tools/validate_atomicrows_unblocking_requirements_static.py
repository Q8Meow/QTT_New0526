#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "ATOMICROWS_UNBLOCKING_REQUIREMENTS_STATIC_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_UNBLOCKING_REQUIREMENTS_STATIC_VALIDATION_FAILED"

BLOCKED_STATUS = "BLOCKED_PENDING_ATOMICROWS_UNBLOCKING_REQUIREMENTS"
NOT_SATISFIED_STATUS = "NOT_SATISFIED"
REQUIREMENT_BLOCKED_STATUS = "BLOCKED"
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
    "requirement_categories",
    "requirement_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_PR28_ATOMICROWS_UNBLOCKING_REQUIREMENTS_REQUIRED_FIXTURE"
    ),
    "fixture_version": "PR28_ATOMICROWS_UNBLOCKING_REQUIREMENTS_REQUIRED_FIXTURE_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
    ),
    "schema_authority_class": "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_AUTHORITY",
    "surface_kind": "ATOMICROWS_UNBLOCKING_REQUIREMENTS_AUDIT_STATIC",
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
    "completion_authority_present",
    "blocker_reduction_present",
    "audit_status",
    "claimed_atomicrows_row_count",
}

AUTHORITY_STATE_CONST_EXPECTATIONS = {
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "bundle_authority_present": False,
    "hash_authority_present": False,
    "completion_authority_present": False,
    "blocker_reduction_present": False,
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
    "OWNER_EXPLICIT_ATOMICROWS_BUNDLE_CREATION_COMMAND": {
        "requirement_id": "OWNER_EXPLICIT_ATOMICROWS_BUNDLE_CREATION_COMMAND",
        "current_status": NOT_SATISFIED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Owner must explicitly authorize later creation of "
            "AtomicRows.bundle.jsonl and AtomicRows.bundle.sha256."
        ),
        "current_pr_assertion": (
            "Current PR does not create bundle/hash and does not satisfy owner "
            "authorization."
        ),
        "blocked_until": "Later explicit owner bundle/hash creation command.",
    },
    "CANONICAL_ATOMIC_PARAMETER_ROW_SPECIFICATION": {
        "requirement_id": "CANONICAL_ATOMIC_PARAMETER_ROW_SPECIFICATION",
        "current_status": NOT_SATISFIED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Exact row schema, required fields, row IDs, sort order, canonical "
            "JSONL serialization, newline policy, key ordering, and UTF-8 byte "
            "rules must be committed as AtomicRows authority."
        ),
        "current_pr_assertion": (
            "Current PR does not invent or assert the canonical row specification."
        ),
        "blocked_until": "Committed source-backed canonical row specification.",
    },
    "AUTHORITATIVE_SOURCE_INPUT_SET": {
        "requirement_id": "AUTHORITATIVE_SOURCE_INPUT_SET",
        "current_status": NOT_SATISFIED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Authoritative input sources for each row must be identified, and "
            "owner policy alone must not be treated as external fact authority."
        ),
        "current_pr_assertion": (
            "Current PR accepts no external facts and identifies no authoritative "
            "row input set."
        ),
        "blocked_until": "Committed source-backed authoritative row input set.",
    },
    "NO_ROW_INVENTION_RULE": {
        "requirement_id": "NO_ROW_INVENTION_RULE",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "No row may be invented to reach 4,183 rows, and completion cannot "
            "be claimed without the actual canonical bundle and hash."
        ),
        "current_pr_assertion": (
            "Current PR enforces no row invention and no synthetic completion."
        ),
        "blocked_until": "Actual canonical bundle/hash and explicit validation gates.",
    },
    "BUNDLE_ABSENCE_BOOTSTRAP_ALLOWED": {
        "requirement_id": "BUNDLE_ABSENCE_BOOTSTRAP_ALLOWED",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Absence of AtomicRows.bundle.jsonl and AtomicRows.bundle.sha256 "
            "remains allowed for bootstrap scaffolds but must not be treated as "
            "completion."
        ),
        "current_pr_assertion": (
            "Current PR preserves bootstrap absence and does not treat absence "
            "as completion."
        ),
        "blocked_until": "Future explicit bundle/hash creation authority.",
    },
    "BUNDLE_CREATION_BLOCKED_NOW": {
        "requirement_id": "BUNDLE_CREATION_BLOCKED_NOW",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Current state remains blocked for AtomicRows bundle creation."
        ),
        "current_pr_assertion": (
            "Current PR does not create AtomicRows.bundle.jsonl and does not "
            "reduce the blocker."
        ),
        "blocked_until": "All unblocking requirements are met in a later step.",
    },
    "HASH_CREATION_BLOCKED_NOW": {
        "requirement_id": "HASH_CREATION_BLOCKED_NOW",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Current state remains blocked for AtomicRows hash creation."
        ),
        "current_pr_assertion": (
            "Current PR does not compute SHA and does not create "
            "AtomicRows.bundle.sha256."
        ),
        "blocked_until": "Canonical bundle authority exists and hash creation is authorized.",
    },
    "COMPLETION_CLAIM_BLOCKED_NOW": {
        "requirement_id": "COMPLETION_CLAIM_BLOCKED_NOW",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "Any 4,183-row completion claim must fail while bundle/hash are absent."
        ),
        "current_pr_assertion": (
            "Current PR creates no AtomicRows completion or row-count completion "
            "claim."
        ),
        "blocked_until": "Canonical bundle/hash exist and completion gates pass.",
    },
    "RUNTIME_AUTHORITY_BLOCKED": {
        "requirement_id": "RUNTIME_AUTHORITY_BLOCKED",
        "current_status": REQUIREMENT_BLOCKED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "AtomicRows inventory cannot create runtime trading, order execution, "
            "connector binding, source acceptance, or profit authority."
        ),
        "current_pr_assertion": (
            "Current PR creates no runtime/live/source/connector/private-state/"
            "order/profit authority."
        ),
        "blocked_until": "Separate future authority and validation outside this audit.",
    },
    "VALIDATION_GATE_REQUIRED_BEFORE_UNBLOCK": {
        "requirement_id": "VALIDATION_GATE_REQUIRED_BEFORE_UNBLOCK",
        "current_status": NOT_SATISFIED_STATUS,
        "required_before_future_bundle_creation": True,
        "required_precondition": (
            "A future bundle/hash creation PR must pass explicit validation gates "
            "before any completion claim."
        ),
        "current_pr_assertion": (
            "Current PR adds only this blocked static audit and does not satisfy "
            "future bundle/hash gates."
        ),
        "blocked_until": "Future bundle/hash creation PR passes explicit gates.",
    },
}

REQUIREMENT_SCOPE_FLAG_EXPECTATIONS = {
    "non_mutating_static_audit": True,
    "deterministic_static_fixture_only": True,
    "canonical_path_presence_only": True,
    "writes_output_files_by_default": False,
    "bundle_absence_bootstrap_allowed": True,
    "bundle_absence_is_completion": False,
    "requirements_complete_explicit_static": True,
    "requires_owner_explicit_bundle_creation_command": True,
    "requires_canonical_row_specification": True,
    "requires_authoritative_source_input_set": True,
    "requires_no_row_invention": True,
    "requires_validation_gate_before_unblock": True,
    "current_state_blocked": True,
    "current_pr_satisfies_any_requirement": False,
    "completion_claim_allowed": False,
    "row_count_completion_claim_allowed": False,
    "blocker_reduction_allowed": False,
    "runtime_use_allowed": False,
    "live_use_allowed": False,
    "source_retrieval_allowed": False,
    "source_acceptance_allowed": False,
    "connector_binding_allowed": False,
    "private_state_fetch_allowed": False,
    "order_execution_allowed": False,
    "sha_freeze_allowed": False,
    "profit_claim_allowed": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "row_invention_enabled",
    "synthetic_row_completion_enabled",
    "generated_authoritative_row_bundle_enabled",
    "completion_claim_enabled",
    "row_count_completion_claim_enabled",
    "blocker_reduction_enabled",
    "requirement_satisfaction_enabled",
    "owner_authorization_substitution_enabled",
    "canonical_row_spec_invention_enabled",
    "authoritative_source_input_set_invention_enabled",
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
    "contains_synthetic_completed_rows",
    "contains_generated_authoritative_row_bundle",
    "claims_atomicrows_completion",
    "claims_4183_row_completion",
    "claims_atomicrows_row_count_completion",
    "claims_blocker_reduction",
    "claims_requirement_satisfaction",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "creates_sha_freeze_authority",
    "creates_freeze_authority",
    "creates_runtime_authority",
    "creates_runtime_trading_authority",
    "creates_live_authority",
    "creates_source_retrieval",
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
}

EXPECTED_SCHEMA_DEFS = {
    "expected_canonical_paths",
    "authority_state",
    "requirement_entry",
    "requirement_categories",
    "requirement_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
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
        label="schema.$defs.requirement_categories",
    )
    properties = _properties(definition)
    for field in sorted(EXPECTED_REQUIREMENTS):
        prop = properties.get(field)
        if not isinstance(prop, dict) or prop.get("$ref") != "#/$defs/requirement_entry":
            failures.append(
                "schema.$defs.requirement_categories."
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
        "requirement_categories": "#/$defs/requirement_categories",
        "requirement_scope_flags": "#/$defs/requirement_scope_flags",
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

    requirement_categories = defs.get("requirement_categories")
    if isinstance(requirement_categories, dict):
        failures.extend(_validate_requirement_categories_schema(requirement_categories))
    else:
        failures.append("schema.$defs.requirement_categories must be an object")

    scope_flags = defs.get("requirement_scope_flags")
    if isinstance(scope_flags, dict):
        failures.extend(
            _validate_boolean_const_schema(
                scope_flags,
                expected=REQUIREMENT_SCOPE_FLAG_EXPECTATIONS,
                label="schema.$defs.requirement_scope_flags",
            )
        )
    else:
        failures.append("schema.$defs.requirement_scope_flags must be an object")

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
    if state.get("canonical_bundle_sha_present") is not sha_present:
        failures.append(
            "atomicrows_authority_state.canonical_bundle_sha_present must match "
            f"filesystem presence {sha_present}"
        )

    if not bundle_present or not sha_present:
        if state.get("audit_status") != BLOCKED_STATUS:
            failures.append(
                "atomicrows_authority_state.audit_status must be "
                f"{BLOCKED_STATUS} while canonical bundle/hash are absent"
            )
        for field in (
            "bundle_authority_present",
            "hash_authority_present",
            "completion_authority_present",
            "blocker_reduction_present",
        ):
            if state.get(field) is not False:
                failures.append(f"atomicrows_authority_state.{field} must be false")
        if state.get("claimed_atomicrows_row_count") != UNBOUND_ROW_COUNT:
            failures.append(
                "atomicrows_authority_state.claimed_atomicrows_row_count must remain "
                f"{UNBOUND_ROW_COUNT} while canonical bundle/hash are absent"
            )
    return failures


def _validate_requirement_categories(categories: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        categories,
        set(EXPECTED_REQUIREMENTS),
        "requirement_categories",
    )
    for requirement_id, expected in sorted(EXPECTED_REQUIREMENTS.items()):
        entry = categories.get(requirement_id)
        if not isinstance(entry, dict):
            failures.append(f"requirement_categories.{requirement_id} must be an object")
            continue
        failures.extend(
            _require_exact_fields(
                entry,
                REQUIREMENT_FIELDS,
                f"requirement_categories.{requirement_id}",
            )
        )
        for field, expected_value in sorted(expected.items()):
            if entry.get(field) != expected_value:
                failures.append(
                    f"requirement_categories.{requirement_id}.{field} "
                    f"must be {expected_value}"
                )
        status = entry.get("current_status")
        if status not in {NOT_SATISFIED_STATUS, REQUIREMENT_BLOCKED_STATUS}:
            failures.append(
                f"requirement_categories.{requirement_id}.current_status must be "
                f"{NOT_SATISFIED_STATUS} or {REQUIREMENT_BLOCKED_STATUS}"
            )
        if status == "SATISFIED":
            failures.append(
                f"requirement_categories.{requirement_id}.current_status must not be SATISFIED"
            )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        set(FORBIDDEN_ACTION_FLAGS)
        | set(NO_CLAIM_FLAGS)
        | {
            field
            for field, expected in REQUIREMENT_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is False
        }
        | {
            "canonical_bundle_present",
            "canonical_bundle_sha_present",
            "bundle_authority_present",
            "hash_authority_present",
            "completion_authority_present",
            "blocker_reduction_present",
        }
    )
    must_be_true = {
        field
        for field, expected in REQUIREMENT_SCOPE_FLAG_EXPECTATIONS.items()
        if expected is True
    }

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key == "audit_status" and item != BLOCKED_STATUS:
            failures.append(f"{path} must be {BLOCKED_STATUS}")
        if key == "claimed_atomicrows_row_count" and item != UNBOUND_ROW_COUNT:
            failures.append(f"{path} must be {UNBOUND_ROW_COUNT}")
        if key == "current_status" and item == "SATISFIED":
            failures.append(f"{path} must not be SATISFIED")
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


def validate_atomicrows_unblocking_requirements_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "atomicrows unblocking requirements fixture",
    )
    for field, value in ROOT_CONST_EXPECTATIONS.items():
        if fixture.get(field) != value:
            failures.append(f"atomicrows unblocking requirements fixture.{field} must be {value}")

    expected_paths, path_failures = _mapping(
        fixture,
        "expected_canonical_paths",
        "atomicrows unblocking requirements fixture",
    )
    failures.extend(path_failures)
    if expected_paths is not None:
        failures.extend(_validate_expected_paths(expected_paths))

    authority_state, authority_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "atomicrows unblocking requirements fixture",
    )
    failures.extend(authority_failures)
    if authority_state is not None:
        failures.extend(_validate_authority_state(authority_state, repo_root=repo_root))

    requirement_categories, requirement_failures = _mapping(
        fixture,
        "requirement_categories",
        "atomicrows unblocking requirements fixture",
    )
    failures.extend(requirement_failures)
    if requirement_categories is not None:
        failures.extend(_validate_requirement_categories(requirement_categories))

    scope_flags, scope_failures = _mapping(
        fixture,
        "requirement_scope_flags",
        "atomicrows unblocking requirements fixture",
    )
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_bool_map(
                scope_flags,
                REQUIREMENT_SCOPE_FLAG_EXPECTATIONS,
                "requirement_scope_flags",
            )
        )

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "atomicrows unblocking requirements fixture",
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
        "atomicrows unblocking requirements fixture",
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
        "ATOMICROWS_UNBLOCKING_REQUIREMENTS_STATIC_NON_MUTATING_AUDIT"
    ]:
        failures.append(
            "atomicrows unblocking requirements fixture.validation_hook_ids must contain only "
            "ATOMICROWS_UNBLOCKING_REQUIREMENTS_STATIC_NON_MUTATING_AUDIT"
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
            validate_atomicrows_unblocking_requirements_fixture(
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
