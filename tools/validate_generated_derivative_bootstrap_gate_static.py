#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "GENERATED_DERIVATIVE_BOOTSTRAP_GATE_STATIC_VALIDATION_OK"
FAILURE_MARKER = "GENERATED_DERIVATIVE_BOOTSTRAP_GATE_STATIC_VALIDATION_FAILED"

GATE_MODE = "BOOTSTRAP_ONLY_NOT_COMPLETION"
DERIVATIVE_ABSENT_STATUS = "NOT_CREATED_ATOMICROWS_BUNDLE_ABSENT"
UNBOUND_ROW_COUNT = "UNBOUND_NO_COMPLETION_AUTHORITY"
COMPLETION_MODE_STATUS = "NOT_SATISFIED_BOOTSTRAP_ONLY"
VALIDATION_HOOK = "GENERATED_DERIVATIVE_BOOTSTRAP_GATE_STATIC_AUDIT"
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
    "gate_mode",
    "deterministic_output",
    "expected_canonical_paths",
    "bootstrap_gate_receipt",
    "completion_mode_requirements",
    "generated_derivative_outputs",
    "generated_derivative_coverage_report",
    "authority_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR31_GENERATED_DERIVATIVE_BOOTSTRAP_GATE_FIXTURE",
    "fixture_version": "PR31_GENERATED_DERIVATIVE_BOOTSTRAP_GATE_FIXTURE_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_GENERATED_DERIVATIVE_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_GENERATED_DERIVATIVE_AUTHORITY"
    ),
    "surface_kind": "GENERATED_DERIVATIVE_BOOTSTRAP_GATE_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "gate_mode": GATE_MODE,
    "deterministic_output": True,
}

EXPECTED_PATH_CONSTS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
}

BOOTSTRAP_GATE_RECEIPT_EXPECTATIONS = {
    "gate_mode": GATE_MODE,
    "atomicrows_bundle_state": "ABSENT",
    "atomicrows_bundle_sha_state": "ABSENT",
    "atomicrows_bundle_absence_allowed": True,
    "atomicrows_hash_absence_allowed": True,
    "completion_mode_claimed": False,
    "completion_mode_satisfied": False,
    "atomicrows_bundle_created": False,
    "atomicrows_hash_created": False,
    "atomicrows_rows_created": False,
    "atomicrows_sha_authority_created": False,
    "declared_completion_row_count": UNBOUND_ROW_COUNT,
    "claims_4183_row_derivative_coverage": False,
    "stage1_packet_schema_unblocked": False,
}

COMPLETION_MODE_REQUIREMENT_EXPECTATIONS = {
    "completion_mode_status": COMPLETION_MODE_STATUS,
    "bundle_must_exist": True,
    "hash_must_exist": True,
    "required_atomicrows_row_count": 4183,
    "atomicrows_validation_required": True,
    "completion_gate_required": True,
    "completion_claim_allowed": False,
    "current_pr_claims_completion": False,
    "current_pr_claims_4183_row_derivative_coverage": False,
}

METADATA_FIELDS = {
    "master_plan_edition",
    "master_plan_sha256",
    "generated_at_utc",
    "generator_version",
    "source_file_path",
}

DECLARED_WRITER_FIELDS = {
    "writer_id",
    "writer_type",
    "writer_version",
    "writes_production_outputs",
    "manual_edit_authority_allowed",
}

OUTPUT_FIELDS = {
    "output_id",
    "output_kind",
    "output_state",
    "derivative_status",
    "metadata",
    "declared_writer_identity",
    "manual_edit_authority_allowed",
    "source_fact_acceptance_claimed",
    "connector_binding_claimed",
    "runtime_authority_claimed",
    "completion_authority_claimed",
}

OUTPUT_CONST_EXPECTATIONS = {
    "output_kind": "ATOMIC_ROW_DERIVATIVE_INDEX",
    "output_state": "NOT_CREATED",
    "derivative_status": DERIVATIVE_ABSENT_STATUS,
    "manual_edit_authority_allowed": False,
    "source_fact_acceptance_claimed": False,
    "connector_binding_claimed": False,
    "runtime_authority_claimed": False,
    "completion_authority_claimed": False,
}

DECLARED_WRITER_CONST_EXPECTATIONS = {
    "writer_type": "STATIC_DECLARED_WRITER",
    "writes_production_outputs": False,
    "manual_edit_authority_allowed": False,
}

COVERAGE_LEDGER_REPORT_EXPECTATIONS = {
    "reporting_allowed": True,
    "blocker_reporting_allowed": True,
    "blocker_reduction_allowed": False,
    "blockers_reduced": False,
    "coverage_state": "BOOTSTRAP_BLOCKED_NO_COMPLETION_COVERAGE_CLAIM",
    "claims_4183_row_derivative_coverage": False,
    "stage1_packet_schema_unblocking_claimed": False,
    "atomicrows_completion_required_before_coverage_claim": True,
}

AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "bootstrap_mode_only": True,
    "static_validation_only": True,
    "non_mutating_validator": True,
    "atomicrows_bundle_absent_allowed_only_with_not_created_status": True,
    "atomicrows_hash_absent_allowed_only_without_sha_authority": True,
    "generated_derivative_coverage_reporting_allowed": True,
    "completion_mode_allowed": False,
    "atomicrows_bundle_creation_allowed": False,
    "atomicrows_bundle_hash_creation_allowed": False,
    "atomicrows_row_creation_allowed": False,
    "atomicrows_sha_authority_allowed": False,
    "completion_authority_allowed": False,
    "generated_derivative_coverage_blocker_reduction_allowed": False,
    "stage1_packet_schema_unblock_allowed": False,
    "manual_edit_authority_allowed": False,
    "source_fact_acceptance_allowed": False,
    "source_retrieval_allowed": False,
    "connector_binding_allowed": False,
    "connector_semantic_binding_allowed": False,
    "private_state_fetch_allowed": False,
    "live_reachability_allowed": False,
    "runtime_trading_allowed": False,
    "order_execution_allowed": False,
    "replay_execution_allowed": False,
    "paper_execution_allowed": False,
    "neural_training_allowed": False,
    "neural_inference_allowed": False,
    "freeze_authority_allowed": False,
    "profit_claim_allowed": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "completion_mode_enabled",
    "row_count_completion_claim_enabled",
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_sha_authority_enabled",
    "atomicrows_row_creation_enabled",
    "actual_row_record_creation_enabled",
    "blocker_reduction_enabled",
    "stage1_packet_schema_unblock_enabled",
    "manual_edit_enabled",
    "source_fact_acceptance_enabled",
    "source_retrieval_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "private_state_fetch_enabled",
    "live_reachability_enabled",
    "runtime_trading_enabled",
    "runtime_execution_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "neural_training_enabled",
    "neural_inference_enabled",
    "freeze_authority_enabled",
    "profit_claim_enabled",
    "profit_evidence_creation_enabled",
}

NO_CLAIM_FLAGS = {
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_atomicrows_row_records",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "claims_atomicrows_sha_authority",
    "creates_atomicrows_rows",
    "creates_atomicrows_row_records",
    "claims_completion_mode",
    "claims_atomicrows_completion",
    "claims_4183_row_derivative_coverage",
    "claims_blocker_reduction",
    "claims_stage1_packet_schema_unblock",
    "permits_manual_editing",
    "claims_source_fact_acceptance",
    "accepts_source_facts",
    "binds_connector",
    "claims_connector_semantic_binding",
    "fetches_private_state",
    "creates_live_reachability",
    "creates_runtime_trading_authority",
    "creates_order_execution_authority",
    "submits_orders",
    "executes_replay",
    "executes_paper",
    "trains_neural_models",
    "runs_neural_models",
    "creates_freeze_authority",
    "creates_profit_evidence",
    "creates_profit_claim",
}

EXPECTED_SCHEMA_DEFS = {
    "expected_canonical_paths",
    "bootstrap_gate_receipt",
    "completion_mode_requirements",
    "generated_derivative_metadata",
    "declared_writer_identity",
    "generated_derivative_output",
    "generated_derivative_coverage_report",
    "authority_scope_flags",
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
    "interactivebrokers",
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


def _validate_const_map(value: dict[str, Any], expected: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(value, set(expected), label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


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
    return _validate_const_map(value, expected_values, label)


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


def _validate_canonical_absence(repo_root: pathlib.Path) -> list[str]:
    root = repo_root.resolve()
    failures: list[str] = []
    bundle_path = _canonical_path(root, CANONICAL_BUNDLE_RELATIVE_PATH)
    sha_path = _canonical_path(root, CANONICAL_BUNDLE_SHA_RELATIVE_PATH)
    if bundle_path.exists():
        failures.append(
            "canonical AtomicRows bundle must remain absent during generated-derivative "
            f"bootstrap validation: {CANONICAL_BUNDLE_RELATIVE_PATH}"
        )
    if sha_path.exists():
        failures.append(
            "canonical AtomicRows bundle hash must remain absent during generated-derivative "
            f"bootstrap validation: {CANONICAL_BUNDLE_SHA_RELATIVE_PATH}"
        )
    return failures


def _validate_schema_surfaces(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("$id") != (
        "https://qtt.local/schemas/master_plan/generated_derivative_bootstrap_gate.schema.json"
    ):
        failures.append("schema.$id must identify the generated derivative bootstrap gate")
    failures.extend(
        _validate_schema_object_contract(
            schema,
            expected_fields=ROOT_FIELDS,
            label="generated derivative bootstrap gate schema",
        )
    )

    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"schema.properties.{field} must be const {expected}")

    properties = _properties(schema)
    expected_refs = {
        "expected_canonical_paths": "#/$defs/expected_canonical_paths",
        "bootstrap_gate_receipt": "#/$defs/bootstrap_gate_receipt",
        "completion_mode_requirements": "#/$defs/completion_mode_requirements",
        "generated_derivative_coverage_report": "#/$defs/generated_derivative_coverage_report",
        "authority_scope_flags": "#/$defs/authority_scope_flags",
        "forbidden_action_flags": "#/$defs/forbidden_action_flags",
        "no_claim_flags": "#/$defs/no_claim_flags",
    }
    for field, expected_ref in sorted(expected_refs.items()):
        prop = properties.get(field, {})
        if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
            failures.append(f"schema.properties.{field} must reference {expected_ref}")

    outputs = properties.get("generated_derivative_outputs", {})
    if not isinstance(outputs, dict) or outputs.get("type") != "array":
        failures.append("schema.generated_derivative_outputs must be an array")
    else:
        if outputs.get("minItems") != 1:
            failures.append("schema.generated_derivative_outputs must require at least one item")
        items = outputs.get("items", {})
        if not isinstance(items, dict) or items.get("$ref") != "#/$defs/generated_derivative_output":
            failures.append(
                "schema.generated_derivative_outputs items must reference generated_derivative_output"
            )

    hook_prop = properties.get("validation_hook_ids", {})
    if not isinstance(hook_prop, dict):
        failures.append("schema.validation_hook_ids must be an array property")
    else:
        if hook_prop.get("type") != "array":
            failures.append("schema.validation_hook_ids must be an array")
        if hook_prop.get("minItems") != 1 or hook_prop.get("maxItems") != 1:
            failures.append("schema.validation_hook_ids must contain exactly one item")
        items = hook_prop.get("items", {})
        if not isinstance(items, dict) or items.get("const") != VALIDATION_HOOK:
            failures.append("schema.validation_hook_ids must contain the static audit hook")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, EXPECTED_SCHEMA_DEFS, "schema.$defs"))

    const_schema_expectations = {
        "expected_canonical_paths": EXPECTED_PATH_CONSTS,
        "bootstrap_gate_receipt": BOOTSTRAP_GATE_RECEIPT_EXPECTATIONS,
        "completion_mode_requirements": COMPLETION_MODE_REQUIREMENT_EXPECTATIONS,
        "generated_derivative_coverage_report": COVERAGE_LEDGER_REPORT_EXPECTATIONS,
        "authority_scope_flags": AUTHORITY_SCOPE_FLAG_EXPECTATIONS,
    }
    for def_name, expected in sorted(const_schema_expectations.items()):
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_const_schema(
                    definition,
                    expected=expected,
                    label=f"schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"schema.$defs.{def_name} must be an object")

    for def_name, expected_fields in {
        "forbidden_action_flags": FORBIDDEN_ACTION_FLAGS,
        "no_claim_flags": NO_CLAIM_FLAGS,
    }.items():
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_bool_map_schema(
                    definition,
                    expected=expected_fields,
                    label=f"schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"schema.$defs.{def_name} must be an object")

    metadata = defs.get("generated_derivative_metadata")
    if isinstance(metadata, dict):
        failures.extend(
            _validate_schema_object_contract(
                metadata,
                expected_fields=METADATA_FIELDS,
                label="schema.$defs.generated_derivative_metadata",
            )
        )
    else:
        failures.append("schema.$defs.generated_derivative_metadata must be an object")

    writer = defs.get("declared_writer_identity")
    if isinstance(writer, dict):
        failures.extend(
            _validate_schema_object_contract(
                writer,
                expected_fields=DECLARED_WRITER_FIELDS,
                label="schema.$defs.declared_writer_identity",
            )
        )
        for field, expected in sorted(DECLARED_WRITER_CONST_EXPECTATIONS.items()):
            if _const_value(writer, field) != expected:
                failures.append(f"schema.$defs.declared_writer_identity.{field} must be const {expected}")
    else:
        failures.append("schema.$defs.declared_writer_identity must be an object")

    output = defs.get("generated_derivative_output")
    if isinstance(output, dict):
        failures.extend(
            _validate_schema_object_contract(
                output,
                expected_fields=OUTPUT_FIELDS,
                label="schema.$defs.generated_derivative_output",
            )
        )
        for field, expected in sorted(OUTPUT_CONST_EXPECTATIONS.items()):
            if _const_value(output, field) != expected:
                failures.append(f"schema.$defs.generated_derivative_output.{field} must be const {expected}")
    else:
        failures.append("schema.$defs.generated_derivative_output must be an object")
    return failures


def _validate_generated_output(output: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(output, OUTPUT_FIELDS, label)
    for field, expected in sorted(OUTPUT_CONST_EXPECTATIONS.items()):
        if output.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")

    if output.get("derivative_status") != DERIVATIVE_ABSENT_STATUS:
        failures.append(
            f"{label}.derivative_status must be {DERIVATIVE_ABSENT_STATUS} "
            "while AtomicRows bundle is absent"
        )

    metadata, metadata_failures = _mapping(output, "metadata", label)
    failures.extend(metadata_failures)
    if metadata is not None:
        failures.extend(_require_exact_fields(metadata, METADATA_FIELDS, f"{label}.metadata"))
        for field in sorted(METADATA_FIELDS):
            if not isinstance(metadata.get(field), str) or not metadata.get(field):
                failures.append(f"{label}.metadata.{field} must be a non-empty string")

    writer, writer_failures = _mapping(output, "declared_writer_identity", label)
    failures.extend(writer_failures)
    if writer is not None:
        failures.extend(_require_exact_fields(writer, DECLARED_WRITER_FIELDS, f"{label}.declared_writer_identity"))
        for field in {"writer_id", "writer_version"}:
            if not isinstance(writer.get(field), str) or not writer.get(field):
                failures.append(f"{label}.declared_writer_identity.{field} must be a non-empty string")
        for field, expected in sorted(DECLARED_WRITER_CONST_EXPECTATIONS.items()):
            if writer.get(field) != expected:
                failures.append(f"{label}.declared_writer_identity.{field} must be {expected}")
    return failures


def _validate_outputs(fixture: dict[str, Any]) -> list[str]:
    outputs = fixture.get("generated_derivative_outputs")
    if not isinstance(outputs, list) or not outputs:
        return ["generated_derivative_outputs must be a non-empty list"]

    failures: list[str] = []
    for index, output in enumerate(outputs):
        label = f"generated_derivative_outputs[{index}]"
        if not isinstance(output, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_validate_generated_output(output, label))
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_FLAGS
        | {
            field
            for field, expected in AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in BOOTSTRAP_GATE_RECEIPT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in COMPLETION_MODE_REQUIREMENT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in COVERAGE_LEDGER_REPORT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in OUTPUT_CONST_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in DECLARED_WRITER_CONST_EXPECTATIONS.items()
            if expected is False
        }
    )
    must_be_true = (
        {
            field
            for field, expected in AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in BOOTSTRAP_GATE_RECEIPT_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in COMPLETION_MODE_REQUIREMENT_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in COVERAGE_LEDGER_REPORT_EXPECTATIONS.items()
            if expected is True
        }
    )

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain AtomicRows row records")
        if key == "gate_mode" and item != GATE_MODE:
            failures.append(f"{path} must be {GATE_MODE}")
        if key == "derivative_status" and item != DERIVATIVE_ABSENT_STATUS:
            failures.append(f"{path} must be {DERIVATIVE_ABSENT_STATUS}")
        if key == "declared_completion_row_count" and item != UNBOUND_ROW_COUNT:
            failures.append(f"{path} must be {UNBOUND_ROW_COUNT}")
        if key == "completion_mode_status" and item != COMPLETION_MODE_STATUS:
            failures.append(f"{path} must be {COMPLETION_MODE_STATUS}")
        if isinstance(item, str):
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_generated_derivative_bootstrap_gate_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "generated derivative bootstrap gate fixture",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(
                f"generated derivative bootstrap gate fixture.{field} must be {expected}"
            )

    paths, path_failures = _mapping(
        fixture,
        "expected_canonical_paths",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(path_failures)
    if paths is not None:
        failures.extend(_validate_const_map(paths, EXPECTED_PATH_CONSTS, "expected_canonical_paths"))

    receipt, receipt_failures = _mapping(
        fixture,
        "bootstrap_gate_receipt",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(receipt_failures)
    if receipt is not None:
        failures.extend(
            _validate_const_map(
                receipt,
                BOOTSTRAP_GATE_RECEIPT_EXPECTATIONS,
                "bootstrap_gate_receipt",
            )
        )

    requirements, requirement_failures = _mapping(
        fixture,
        "completion_mode_requirements",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(requirement_failures)
    if requirements is not None:
        failures.extend(
            _validate_const_map(
                requirements,
                COMPLETION_MODE_REQUIREMENT_EXPECTATIONS,
                "completion_mode_requirements",
            )
        )

    failures.extend(_validate_outputs(fixture))

    coverage, coverage_failures = _mapping(
        fixture,
        "generated_derivative_coverage_report",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(coverage_failures)
    if coverage is not None:
        failures.extend(
            _validate_const_map(
                coverage,
                COVERAGE_LEDGER_REPORT_EXPECTATIONS,
                "generated_derivative_coverage_report",
            )
        )

    authority, authority_failures = _mapping(
        fixture,
        "authority_scope_flags",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(authority_failures)
    if authority is not None:
        failures.extend(
            _validate_bool_map(
                authority,
                AUTHORITY_SCOPE_FLAG_EXPECTATIONS,
                "authority_scope_flags",
            )
        )

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "generated derivative bootstrap gate fixture",
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

    no_claims, no_claim_failures = _mapping(
        fixture,
        "no_claim_flags",
        "generated derivative bootstrap gate fixture",
    )
    failures.extend(no_claim_failures)
    if no_claims is not None:
        failures.extend(
            _validate_bool_map(
                no_claims,
                NO_CLAIM_FLAGS,
                "no_claim_flags",
            )
        )

    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")

    failures.extend(_validate_canonical_absence(repo_root))
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
        failures.extend(_validate_schema_surfaces(schema))
    if fixture is not None:
        failures.extend(
            validate_generated_derivative_bootstrap_gate_fixture(
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
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
