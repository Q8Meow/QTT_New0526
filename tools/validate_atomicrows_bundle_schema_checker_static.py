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

SUCCESS_MARKER = "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_VALIDATION_FAILED"

BOOTSTRAP_MODE = "BOOTSTRAP_ABSENT_BLOCKED"
CHECK_STATUS = "BLOCKED_ATOMICROWS_BUNDLE_NOT_CREATED"
COMPLETION_REQUIREMENT_STATUS = "DECLARED_NOT_SATISFIED_BOOTSTRAP_BLOCKED"
UNBOUND_ROW_COUNT = "UNBOUND_NO_BUNDLE_AUTHORITY"
ROW_SCHEMA_ID = "https://qtt.local/schemas/atomicrows/atomic_parameter_row.schema.json"
BUNDLE_SCHEMA_ID = "https://qtt.local/schemas/atomicrows/atomic_row_bundle.schema.json"
ROW_SCHEMA_STATIC_REF = "QTT_SCHEMA_ATOMIC_PARAMETER_ROW_V1"

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
    "checker_mode",
    "execution",
    "deterministic_output",
    "check_status",
    "expected_canonical_paths",
    "bootstrap_absent_receipt",
    "completion_mode_requirements",
    "checker_capabilities",
    "atomicrows_authority_state",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR30_ATOMICROWS_BUNDLE_SCHEMA_CHECKER_BOOTSTRAP_ABSENT_FIXTURE",
    "fixture_version": "PR30_ATOMICROWS_BUNDLE_SCHEMA_CHECKER_BOOTSTRAP_ABSENT_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
    ),
    "schema_authority_class": "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_AUTHORITY",
    "surface_kind": "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_BOOTSTRAP_STATIC",
    "mode": "SOURCE_REQUIRED",
    "checker_mode": BOOTSTRAP_MODE,
    "execution": "DISABLED",
    "deterministic_output": True,
    "check_status": CHECK_STATUS,
}

EXPECTED_PATH_FIELDS = {
    "canonical_bundle_path",
    "canonical_bundle_sha_path",
}

EXPECTED_PATH_CONSTS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
}

BOOTSTRAP_RECEIPT_EXPECTATIONS = {
    "mode": BOOTSTRAP_MODE,
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_state": "NOT_CREATED",
    "canonical_bundle_sha_state": "NOT_CREATED",
    "bundle_absence_valid_blocked": True,
    "hash_absence_valid_blocked": True,
    "bootstrap_absent_mode_explicit": True,
    "completion_mode_satisfied": False,
    "created_bundle": False,
    "created_hash": False,
    "created_rows": False,
    "created_sha_authority": False,
    "reduced_blockers": False,
    "check_status": CHECK_STATUS,
}

COMPLETION_REQUIREMENT_EXPECTATIONS = {
    "completion_mode_status": COMPLETION_REQUIREMENT_STATUS,
    "bundle_must_exist": True,
    "hash_must_exist": True,
    "required_launch_row_count": 4183,
    "deterministic_jsonl_one_object_per_line_required": True,
    "deterministic_jsonl_one_object_per_line_parsing_required": True,
    "rows_sorted_by_atomic_parameter_row_id_required": True,
    "utf8_encoding_required": True,
    "lf_newline_required": True,
    "atomic_parameter_row_schema_validity_required": True,
    "row_schema_path": "schemas/atomicrows/atomic_parameter_row.schema.json",
    "row_schema_static_ref": ROW_SCHEMA_STATIC_REF,
    "completion_mode_satisfied": False,
    "current_pr_creates_completion_authority": False,
}

CHECKER_CAPABILITY_EXPECTATIONS = {
    "validates_static_schema_contract": True,
    "validates_bootstrap_absence": True,
    "emits_blocked_receipt": True,
    "creates_or_mutates_files": False,
    "creates_atomicrows_bundle": False,
    "creates_atomicrows_bundle_hash": False,
    "creates_atomicrows_rows": False,
    "computes_real_atomicrows_bundle_sha": False,
    "creates_sha_authority": False,
    "mutates_canonical_bundle_in_place": False,
    "normalizes_canonical_bundle_in_place": False,
    "repairs_canonical_bundle_in_place": False,
    "rewrites_atomicrows_bundle_hash": False,
    "reduces_blockers": False,
    "claims_source_fact_acceptance": False,
    "allows_source_fact_acceptance": False,
    "allows_connector_binding": False,
    "allows_private_state_fetch": False,
    "allows_live_reachability": False,
    "allows_replay_or_paper_success": False,
    "allows_order_execution": False,
    "allows_runtime_trading_authority": False,
    "allows_profit_evidence": False,
    "uses_network_io": False,
}

AUTHORITY_STATE_CONST_EXPECTATIONS = {
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "bundle_authority_present": False,
    "hash_authority_present": False,
    "sha_authority_present": False,
    "row_creation_authority_present": False,
    "completion_authority_present": False,
    "blocker_reduction_present": False,
    "runtime_authority_present": False,
    "live_reachability_authority_present": False,
    "source_fact_acceptance_authority_present": False,
    "connector_authority_present": False,
    "private_state_authority_present": False,
    "order_execution_authority_present": False,
    "freeze_authority_present": False,
    "profit_authority_present": False,
    "check_status": CHECK_STATUS,
    "claimed_atomicrows_row_count": UNBOUND_ROW_COUNT,
}

FORBIDDEN_ACTION_FLAGS = {
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_sha_authority_enabled",
    "atomicrows_row_creation_enabled",
    "actual_row_record_creation_enabled",
    "canonical_row_record_creation_enabled",
    "invented_row_creation_enabled",
    "completion_claim_enabled",
    "row_count_completion_claim_enabled",
    "blocker_reduction_enabled",
    "mutate_canonical_bundle_enabled",
    "normalize_canonical_bundle_in_place_enabled",
    "repair_canonical_bundle_in_place_enabled",
    "rewrite_atomicrows_bundle_hash_enabled",
    "source_retrieval_enabled",
    "source_fact_acceptance_enabled",
    "connector_binding_enabled",
    "private_state_fetch_enabled",
    "live_reachability_enabled",
    "runtime_trading_enabled",
    "runtime_execution_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "canary_execution_enabled",
    "arbitrage_execution_enabled",
    "full_live_execution_enabled",
    "scaled_live_execution_enabled",
    "day1_launch_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "freeze_authority_enabled",
    "neural_training_enabled",
    "neural_inference_enabled",
    "network_io_enabled",
    "external_repo_clone_enabled",
    "package_install_script_enabled",
    "profit_claim_enabled",
    "profit_evidence_creation_enabled",
}

NO_CLAIM_FLAGS = {
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_atomicrows_rows",
    "contains_atomicrows_row_records",
    "contains_canonical_row_records",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "claims_sha_authority",
    "creates_atomicrows_rows",
    "creates_canonical_row_records",
    "claims_4183_row_completion",
    "claims_atomicrows_row_count_completion",
    "claims_atomicrows_completion",
    "claims_blocker_reduction",
    "creates_runtime_authority",
    "creates_runtime_trading_authority",
    "creates_live_authority",
    "creates_live_reachability",
    "creates_source_retrieval",
    "accepts_source_facts",
    "creates_source_fact_acceptance",
    "binds_connector",
    "fetches_private_state",
    "executes_replay",
    "executes_paper",
    "executes_canary",
    "executes_arbitrage",
    "executes_full_live",
    "executes_scaled_live",
    "executes_day1_launch",
    "submits_orders",
    "creates_order_execution_authority",
    "creates_freeze_authority",
    "creates_profit_evidence",
    "creates_profit_claim",
    "creates_network_io",
    "trains_neural_models",
    "runs_neural_models",
    "clones_external_repos",
    "runs_package_install_scripts",
}

EXPECTED_SCHEMA_DEFS = {
    "expected_canonical_paths",
    "bootstrap_absent_receipt",
    "completion_mode_requirements",
    "checker_capabilities",
    "authority_state",
    "forbidden_action_flags",
    "no_claim_flags",
}

ROW_SCHEMA_FIELDS = {
    "atomic_parameter_row_id",
    "schema_version",
    "row_authority_class",
    "parameter_key",
    "parameter_value",
    "source_evidence",
    "canonicalization",
}

ROW_SCHEMA_DEFS = {
    "parameter_key",
    "scalar_parameter_value",
    "source_evidence",
    "canonicalization",
}

FORBIDDEN_ROW_SCHEMA_FIELD_FRAGMENTS = {
    "runtime",
    "live",
    "profit",
    "order_execution",
    "order_authority",
    "connector_binding",
    "private_state",
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
    "canonical_row_record",
    "canonical_row_records",
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
            failures.append(
                f"{label} has unexpected required fields: {', '.join(unexpected_required)}"
            )
        if len(required) != len(required_fields):
            failures.append(f"{label}.required must not contain duplicate fields")
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


def _validate_bool_map_schema(
    definition: dict[str, Any],
    *,
    expected: dict[str, bool] | set[str],
    label: str,
) -> list[str]:
    expected_values = (
        {field: False for field in expected}
        if isinstance(expected, set)
        else dict(expected)
    )
    return _validate_const_schema(definition, expected=expected_values, label=label)


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


def _validate_const_map(
    value: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> list[str]:
    failures = _require_exact_fields(value, set(expected), label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def _mapping(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


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


def _validate_row_schema(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("$id") != ROW_SCHEMA_ID:
        failures.append(f"row schema.$id must be {ROW_SCHEMA_ID}")
    failures.extend(
        _validate_schema_object_contract(
            schema,
            expected_fields=ROW_SCHEMA_FIELDS,
            label="row schema",
        )
    )

    properties = _properties(schema)
    atomic_id = properties.get("atomic_parameter_row_id", {})
    if not isinstance(atomic_id, dict) or atomic_id.get("type") != "string":
        failures.append("row schema.atomic_parameter_row_id must be a string")
    if not isinstance(atomic_id, dict) or atomic_id.get("pattern") != (
        "^atomic_parameter_row_[0-9]{4}$"
    ):
        failures.append("row schema.atomic_parameter_row_id must use the canonical id pattern")
    if _const_value(schema, "schema_version") != "atomic_parameter_row.v1":
        failures.append("row schema.schema_version must be const atomic_parameter_row.v1")

    row_authority = properties.get("row_authority_class", {})
    if not isinstance(row_authority, dict) or row_authority.get("enum") != [
        "SOURCE_BACKED_ATOMIC_PARAMETER_ROW"
    ]:
        failures.append("row schema.row_authority_class must fail closed to source-backed rows")

    expected_refs = {
        "parameter_key": "#/$defs/parameter_key",
        "parameter_value": "#/$defs/scalar_parameter_value",
        "source_evidence": "#/$defs/source_evidence",
        "canonicalization": "#/$defs/canonicalization",
    }
    for field, expected_ref in sorted(expected_refs.items()):
        prop = properties.get(field, {})
        if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
            failures.append(f"row schema.properties.{field} must reference {expected_ref}")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["row schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, ROW_SCHEMA_DEFS, "row schema.$defs"))

    parameter_key = defs.get("parameter_key")
    if isinstance(parameter_key, dict):
        failures.extend(
            _validate_schema_object_contract(
                parameter_key,
                expected_fields={"namespace", "name"},
                label="row schema.$defs.parameter_key",
            )
        )
    else:
        failures.append("row schema.$defs.parameter_key must be an object")

    source_evidence = defs.get("source_evidence")
    if isinstance(source_evidence, dict):
        failures.extend(
            _validate_schema_object_contract(
                source_evidence,
                expected_fields={
                    "source_evidence_ids",
                    "source_fact_acceptance_required_before_bundle_authority",
                },
                label="row schema.$defs.source_evidence",
            )
        )
        if _const_value(
            source_evidence,
            "source_fact_acceptance_required_before_bundle_authority",
        ) is not True:
            failures.append(
                "row schema source evidence must require source acceptance before authority"
            )
    else:
        failures.append("row schema.$defs.source_evidence must be an object")

    canonicalization = defs.get("canonicalization")
    if isinstance(canonicalization, dict):
        failures.extend(
            _validate_schema_object_contract(
                canonicalization,
                expected_fields={
                    "sorted_by",
                    "jsonl_one_object_per_line",
                    "utf8_encoding",
                    "newline_policy",
                },
                label="row schema.$defs.canonicalization",
            )
        )
        for field, expected in {
            "sorted_by": "atomic_parameter_row_id",
            "jsonl_one_object_per_line": True,
            "utf8_encoding": "UTF-8",
            "newline_policy": "LF",
        }.items():
            if _const_value(canonicalization, field) != expected:
                failures.append(
                    f"row schema.$defs.canonicalization.{field} must be const {expected}"
                )
    else:
        failures.append("row schema.$defs.canonicalization must be an object")

    scalar_value = defs.get("scalar_parameter_value")
    if isinstance(scalar_value, dict):
        one_of = scalar_value.get("oneOf")
        expected_types = {"string", "number", "boolean"}
        observed_types = {
            entry.get("type")
            for entry in one_of
            if isinstance(entry, dict)
        } if isinstance(one_of, list) else set()
        if observed_types != expected_types:
            failures.append(
                "row schema.$defs.scalar_parameter_value must allow only JSON scalar values"
            )
    else:
        failures.append("row schema.$defs.scalar_parameter_value must be an object")

    for path, key, _item in _walk(schema, "row schema"):
        lowered = key.lower()
        for fragment in sorted(FORBIDDEN_ROW_SCHEMA_FIELD_FRAGMENTS):
            if fragment in lowered:
                failures.append(
                    f"{path} must not define runtime/live/order/profit authority fields"
                )
    return failures


def _validate_bundle_schema(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("$id") != BUNDLE_SCHEMA_ID:
        failures.append(f"bundle schema.$id must be {BUNDLE_SCHEMA_ID}")
    failures.extend(
        _validate_schema_object_contract(
            schema,
            expected_fields=ROOT_FIELDS,
            label="bundle schema",
        )
    )

    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"bundle schema.properties.{field} must be const {expected}")

    properties = _properties(schema)
    expected_refs = {
        "expected_canonical_paths": "#/$defs/expected_canonical_paths",
        "bootstrap_absent_receipt": "#/$defs/bootstrap_absent_receipt",
        "completion_mode_requirements": "#/$defs/completion_mode_requirements",
        "checker_capabilities": "#/$defs/checker_capabilities",
        "atomicrows_authority_state": "#/$defs/authority_state",
        "forbidden_action_flags": "#/$defs/forbidden_action_flags",
        "no_claim_flags": "#/$defs/no_claim_flags",
    }
    for field, expected_ref in sorted(expected_refs.items()):
        prop = properties.get(field, {})
        if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
            failures.append(f"bundle schema.properties.{field} must reference {expected_ref}")

    hook_prop = properties.get("validation_hook_ids", {})
    if not isinstance(hook_prop, dict):
        failures.append("bundle schema.properties.validation_hook_ids must be an object")
    else:
        if hook_prop.get("type") != "array":
            failures.append("bundle schema.validation_hook_ids must be an array")
        if hook_prop.get("minItems") != 1 or hook_prop.get("maxItems") != 1:
            failures.append("bundle schema.validation_hook_ids must contain exactly one item")
        items = hook_prop.get("items", {})
        if not isinstance(items, dict) or items.get("const") != (
            "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_BOOTSTRAP_AUDIT"
        ):
            failures.append(
                "bundle schema.validation_hook_ids must contain the bootstrap audit hook"
            )

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["bundle schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, EXPECTED_SCHEMA_DEFS, "bundle schema.$defs"))

    schema_def_expectations = {
        "expected_canonical_paths": EXPECTED_PATH_CONSTS,
        "bootstrap_absent_receipt": BOOTSTRAP_RECEIPT_EXPECTATIONS,
        "completion_mode_requirements": COMPLETION_REQUIREMENT_EXPECTATIONS,
        "checker_capabilities": CHECKER_CAPABILITY_EXPECTATIONS,
        "authority_state": AUTHORITY_STATE_CONST_EXPECTATIONS,
    }
    for def_name, expected in sorted(schema_def_expectations.items()):
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_const_schema(
                    definition,
                    expected=expected,
                    label=f"bundle schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"bundle schema.$defs.{def_name} must be an object")

    for def_name, expected in {
        "forbidden_action_flags": FORBIDDEN_ACTION_FLAGS,
        "no_claim_flags": NO_CLAIM_FLAGS,
    }.items():
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_bool_map_schema(
                    definition,
                    expected=expected,
                    label=f"bundle schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"bundle schema.$defs.{def_name} must be an object")
    return failures


def _validate_expected_paths(paths: dict[str, Any]) -> list[str]:
    return _validate_const_map(paths, EXPECTED_PATH_CONSTS, "expected_canonical_paths")


def _validate_bootstrap_receipt(receipt: dict[str, Any]) -> list[str]:
    return _validate_const_map(
        receipt,
        BOOTSTRAP_RECEIPT_EXPECTATIONS,
        "bootstrap_absent_receipt",
    )


def _validate_completion_requirements(requirements: dict[str, Any]) -> list[str]:
    return _validate_const_map(
        requirements,
        COMPLETION_REQUIREMENT_EXPECTATIONS,
        "completion_mode_requirements",
    )


def _validate_checker_capabilities(capabilities: dict[str, Any]) -> list[str]:
    return _validate_bool_map(
        capabilities,
        CHECKER_CAPABILITY_EXPECTATIONS,
        "checker_capabilities",
    )


def _validate_authority_state(
    state: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _validate_const_map(
        state,
        AUTHORITY_STATE_CONST_EXPECTATIONS,
        "atomicrows_authority_state",
    )

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
            label="bootstrap validation",
        )
    )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        set(FORBIDDEN_ACTION_FLAGS)
        | set(NO_CLAIM_FLAGS)
        | {
            field
            for field, expected in CHECKER_CAPABILITY_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in AUTHORITY_STATE_CONST_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in BOOTSTRAP_RECEIPT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in COMPLETION_REQUIREMENT_EXPECTATIONS.items()
            if expected is False
        }
    )
    must_be_true = (
        {
            field
            for field, expected in CHECKER_CAPABILITY_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in BOOTSTRAP_RECEIPT_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in COMPLETION_REQUIREMENT_EXPECTATIONS.items()
            if expected is True
        }
    )

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain actual AtomicRows row records")
        if key == "claimed_atomicrows_row_count" and item != UNBOUND_ROW_COUNT:
            failures.append(f"{path} must be {UNBOUND_ROW_COUNT}")
        if key in {"check_status"} and item != CHECK_STATUS:
            failures.append(f"{path} must be {CHECK_STATUS}")
        if key == "completion_mode_status" and item != COMPLETION_REQUIREMENT_STATUS:
            failures.append(f"{path} must be {COMPLETION_REQUIREMENT_STATUS}")
        if key == "checker_mode" and item != BOOTSTRAP_MODE:
            failures.append(f"{path} must be {BOOTSTRAP_MODE}")
        if isinstance(item, str):
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_atomicrows_bundle_schema_checker_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "atomicrows bundle schema checker fixture",
    )
    for field, value in ROOT_CONST_EXPECTATIONS.items():
        if fixture.get(field) != value:
            failures.append(
                "atomicrows bundle schema checker fixture."
                f"{field} must be {value}"
            )

    expected_paths, path_failures = _mapping(
        fixture,
        "expected_canonical_paths",
        "atomicrows bundle schema checker fixture",
    )
    failures.extend(path_failures)
    if expected_paths is not None:
        failures.extend(_validate_expected_paths(expected_paths))

    bootstrap_receipt, receipt_failures = _mapping(
        fixture,
        "bootstrap_absent_receipt",
        "atomicrows bundle schema checker fixture",
    )
    failures.extend(receipt_failures)
    if bootstrap_receipt is not None:
        failures.extend(_validate_bootstrap_receipt(bootstrap_receipt))

    completion_requirements, completion_failures = _mapping(
        fixture,
        "completion_mode_requirements",
        "atomicrows bundle schema checker fixture",
    )
    failures.extend(completion_failures)
    if completion_requirements is not None:
        failures.extend(_validate_completion_requirements(completion_requirements))

    checker_capabilities, capability_failures = _mapping(
        fixture,
        "checker_capabilities",
        "atomicrows bundle schema checker fixture",
    )
    failures.extend(capability_failures)
    if checker_capabilities is not None:
        failures.extend(_validate_checker_capabilities(checker_capabilities))

    authority_state, authority_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "atomicrows bundle schema checker fixture",
    )
    failures.extend(authority_failures)
    if authority_state is not None:
        failures.extend(_validate_authority_state(authority_state, repo_root=repo_root))

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "atomicrows bundle schema checker fixture",
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
        "atomicrows bundle schema checker fixture",
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
        "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_BOOTSTRAP_AUDIT"
    ]:
        failures.append(
            "atomicrows bundle schema checker fixture.validation_hook_ids must "
            "contain only ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_BOOTSTRAP_AUDIT"
        )

    failures.extend(_validate_no_forbidden_claims(fixture))
    return failures


def validate_static_surface(
    *,
    row_schema_path: pathlib.Path,
    bundle_schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    row_schema, row_schema_failures = _load_json(row_schema_path)
    bundle_schema, bundle_schema_failures = _load_json(bundle_schema_path)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(row_schema_failures)
    failures.extend(bundle_schema_failures)
    failures.extend(fixture_failures)

    if row_schema is not None:
        failures.extend(_validate_row_schema(row_schema))
    if bundle_schema is not None:
        failures.extend(_validate_bundle_schema(bundle_schema))
    if fixture is not None:
        failures.extend(
            validate_atomicrows_bundle_schema_checker_fixture(
                fixture,
                repo_root=repo_root,
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--row-schema", required=True)
    parser.add_argument("--bundle-schema", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        row_schema_path=pathlib.Path(args.row_schema),
        bundle_schema_path=pathlib.Path(args.bundle_schema),
        fixture_path=pathlib.Path(args.fixture),
        repo_root=pathlib.Path(args.repo_root),
    )
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
