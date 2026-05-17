#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "ATOMICROWS_READINESS_STATIC_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_READINESS_STATIC_VALIDATION_FAILED"

BLOCKED_STATUS = "BLOCKED_PENDING_ATOMICROWS_BUNDLE_AUTHORITY"
CANONICAL_BUNDLE_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)
UNBOUND_ROW_COUNT = "UNBOUND_NO_BUNDLE_AUTHORITY"

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
    "atomicrows_authority_state",
    "readiness_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR27_ATOMICROWS_READINESS_BLOCKED_FIXTURE",
    "fixture_version": "PR27_ATOMICROWS_READINESS_BLOCKED_FIXTURE_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
    ),
    "schema_authority_class": "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_AUTHORITY",
    "surface_kind": "ATOMICROWS_READINESS_BLOCKER_AUDIT_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "audit_status": BLOCKED_STATUS,
}

AUTHORITY_STATE_FIELDS = {
    "canonical_bundle_path",
    "canonical_bundle_sha_path",
    "canonical_bundle_present",
    "canonical_bundle_sha_present",
    "bundle_authority_present",
    "completion_authority_present",
    "audit_status",
    "claimed_atomicrows_row_count",
}

AUTHORITY_STATE_CONST_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "bundle_authority_present": False,
    "completion_authority_present": False,
    "audit_status": BLOCKED_STATUS,
    "claimed_atomicrows_row_count": UNBOUND_ROW_COUNT,
}

READINESS_SCOPE_FLAG_EXPECTATIONS = {
    "non_mutating_static_audit": True,
    "deterministic_static_fixture_only": True,
    "canonical_path_presence_only": True,
    "bootstrap_absence_allowed": True,
    "bundle_authority_required_before_completion": True,
    "blocked_pending_bundle_authority": True,
    "writes_output_files_by_default": False,
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
    "runtime_enabled",
    "runtime_execution_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "live_enabled",
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "private_state_fetch_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "sha_freeze_enabled",
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
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "creates_sha_freeze_authority",
    "creates_runtime_authority",
    "creates_runtime_trading_authority",
    "creates_live_authority",
    "creates_source_retrieval",
    "accepts_source_facts",
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
}

EXPECTED_SCHEMA_DEFS = {
    "authority_state",
    "readiness_scope_flags",
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


def _required(definition: dict[str, Any]) -> set[str]:
    required = definition.get("required", [])
    return set(required) if isinstance(required, list) else set()


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
        "atomicrows_authority_state": "#/$defs/authority_state",
        "readiness_scope_flags": "#/$defs/readiness_scope_flags",
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

    readiness_scope = defs.get("readiness_scope_flags")
    if isinstance(readiness_scope, dict):
        failures.extend(
            _validate_boolean_const_schema(
                readiness_scope,
                expected=READINESS_SCOPE_FLAG_EXPECTATIONS,
                label="schema.$defs.readiness_scope_flags",
            )
        )
    else:
        failures.append("schema.$defs.readiness_scope_flags must be an object")

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
        if state.get("bundle_authority_present") is not False:
            failures.append("atomicrows_authority_state.bundle_authority_present must be false")
        if state.get("completion_authority_present") is not False:
            failures.append("atomicrows_authority_state.completion_authority_present must be false")
        if state.get("claimed_atomicrows_row_count") != UNBOUND_ROW_COUNT:
            failures.append(
                "atomicrows_authority_state.claimed_atomicrows_row_count must remain "
                f"{UNBOUND_ROW_COUNT} while canonical bundle/hash are absent"
            )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        set(FORBIDDEN_ACTION_FLAGS)
        | set(NO_CLAIM_FLAGS)
        | {
            field
            for field, expected in READINESS_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is False
        }
        | {
            "canonical_bundle_present",
            "canonical_bundle_sha_present",
            "bundle_authority_present",
            "completion_authority_present",
        }
    )
    must_be_true = {
        field
        for field, expected in READINESS_SCOPE_FLAG_EXPECTATIONS.items()
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


def validate_atomicrows_readiness_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "atomicrows readiness fixture")
    for field, value in ROOT_CONST_EXPECTATIONS.items():
        if fixture.get(field) != value:
            failures.append(f"atomicrows readiness fixture.{field} must be {value}")

    authority_state, authority_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "atomicrows readiness fixture",
    )
    failures.extend(authority_failures)
    if authority_state is not None:
        failures.extend(_validate_authority_state(authority_state, repo_root=repo_root))

    readiness_scope, readiness_failures = _mapping(
        fixture,
        "readiness_scope_flags",
        "atomicrows readiness fixture",
    )
    failures.extend(readiness_failures)
    if readiness_scope is not None:
        failures.extend(
            _validate_bool_map(
                readiness_scope,
                READINESS_SCOPE_FLAG_EXPECTATIONS,
                "readiness_scope_flags",
            )
        )

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "atomicrows readiness fixture",
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
        "atomicrows readiness fixture",
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
        "ATOMICROWS_READINESS_STATIC_NON_MUTATING_AUDIT"
    ]:
        failures.append(
            "atomicrows readiness fixture.validation_hook_ids must contain only "
            "ATOMICROWS_READINESS_STATIC_NON_MUTATING_AUDIT"
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
            validate_atomicrows_readiness_fixture(fixture, repo_root=repo_root)
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
