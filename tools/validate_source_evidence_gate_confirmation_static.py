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

SUCCESS_MARKER = "SOURCE_EVIDENCE_GATE_CONFIRMATION_STATIC_VALIDATION_OK"
FAILURE_MARKER = "SOURCE_EVIDENCE_GATE_CONFIRMATION_STATIC_VALIDATION_FAILED"

CONFIRMATION_STATUS = (
    "CONFIRMED_BLOCKED_PENDING_TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE"
)
GATE_AUTHORITY_CLASS = (
    "STATIC_AUDIT_ONLY_NOT_SOURCE_RETRIEVAL_NOT_SOURCE_ACCEPTANCE_NOT_CONNECTOR_AUTHORITY"
)
AUDIT_HOOK_ID = "SOURCE_EVIDENCE_GATE_CONFIRMATION_STATIC_NON_MUTATING_AUDIT"
COMMAND_MAPPING = "COMMAND_12_VERIFY_SOURCE_EVIDENCE_GATE_AND_CONNECTOR_SEMANTIC_BLOCKS"
ACCEPTED_PACKET_SCHEMA_REF = (
    "schemas/source_evidence/source_evidence.schema.json#/$defs/accepted_source_packet"
)
BLOCKED_SEMANTIC_STATUS = (
    "BLOCKED_PENDING_EXACT_TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE"
)
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
    "example_authority_class",
    "schema_authority_class",
    "surface_kind",
    "surface_version",
    "mode",
    "execution",
    "deterministic_output",
    "gate_authority_class",
    "confirmation_status",
    "fixture_no_claim_flags",
    "no_claim_flags",
    "source_evidence_gate_confirmation",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR32_SOURCE_EVIDENCE_GATE_CONFIRMATION_BLOCKED_FIXTURE",
    "fixture_version": "PR32_SOURCE_EVIDENCE_GATE_CONFIRMATION_BLOCKED_FIXTURE_V1",
    "fixture_authority_class": "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT",
    "example_authority_class": "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT",
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_SOURCE_EVIDENCE_GATE_AUTHORITY"
    ),
    "surface_kind": "SOURCE_EVIDENCE_GATE_CONFIRMATION_STATIC_AUDIT",
    "surface_version": "PR32_SOURCE_EVIDENCE_GATE_CONFIRMATION_SCHEMA_V1",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "gate_authority_class": GATE_AUTHORITY_CLASS,
    "confirmation_status": CONFIRMATION_STATUS,
}

SOURCE_FIXTURE_NO_CLAIM_FLAGS = {
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_evidence",
    "unlocks_connector_semantics",
    "creates_runtime_cash_receipts",
    "creates_live_reachability",
    "executes_orders",
    "creates_profit_evidence",
}

SOURCE_ROOT_NO_CLAIM_FLAGS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "runtime_authority",
    "runtime_cash_fetch_authority",
    "private_state_fetch_authority",
    "order_execution_authority",
    "replay_paper_live_execution_authority",
    "network_io_authority",
    "sha_freeze_authority",
    "profit_claim_authority",
}

GATE_FIELDS = {
    "audit_id",
    "audit_authority_class",
    "command_mapping",
    "mode",
    "execution",
    "deterministic_output",
    "gate_status",
    "accepted_packet_schema_contract",
    "source_required_placeholder_contract",
    "connector_semantic_block_contract",
    "blocked_semantic_families",
    "runtime_block_contract",
    "atomicrows_authority_state",
    "forbidden_action_flags",
    "audit_no_claim_flags",
    "validation_hook_ids",
}

GATE_CONST_EXPECTATIONS = {
    "audit_id": "SYNTHETIC_PR32_SOURCE_EVIDENCE_GATE_CONFIRMATION_AUDIT",
    "audit_authority_class": GATE_AUTHORITY_CLASS,
    "command_mapping": COMMAND_MAPPING,
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "gate_status": CONFIRMATION_STATUS,
}

ACCEPTED_PACKET_SCHEMA_CONTRACT_EXPECTATIONS = {
    "accepted_source_packet_schema_ref": ACCEPTED_PACKET_SCHEMA_REF,
    "accepted_packet_schema_required": True,
    "target_field_specific_packet_required": True,
    "exact_target_field_authorization_required": True,
    "exact_packet_fields_required_before_semantic_acceptance": True,
    "accepted_packet_validation_required_before_semantic_binding": True,
    "accepted_packet_creation_by_this_audit": False,
    "source_retrieval_execution_claimed": False,
    "source_acceptance_execution_claimed": False,
    "source_fact_acceptance_claimed": False,
    "connector_semantic_binding_claimed": False,
}

SOURCE_REQUIRED_PLACEHOLDER_EXPECTATIONS = {
    "source_required_value": "SOURCE_REQUIRED",
    "placeholder_state_without_packet": "SOURCE_REQUIRED_PRESERVED",
    "no_accepted_target_field_packet_state": "NO_ACCEPTED_SOURCE_EVIDENCE_PRESENT",
    "placeholders_preserved_without_target_field_packet": True,
    "weakening_allowed": False,
    "replacement_with_source_dependent_value_allowed": False,
    "connector_semantic_values_remain_source_required": True,
    "venue_api_fields_remain_source_required": True,
    "fees_ticks_rate_limits_remain_source_required": True,
    "order_settlement_private_replay_historical_remain_source_required": True,
}

CONNECTOR_SEMANTIC_BLOCK_EXPECTATIONS = {
    "accepted_source_evidence_present_for_target_field": False,
    "connector_binding_blocked_without_target_field_packet": True,
    "connector_binding_allowed_without_target_field_packet": False,
    "connector_semantic_value_population_allowed_without_target_field_packet": False,
    "target_field_packet_validation_required": True,
    "target_field_packet_schema_validation_required": True,
    "target_field_exact_match_required": True,
    "wildcard_packet_unlock_allowed": False,
    "venue_level_packet_unlock_allowed": False,
    "source_dependent_values_blocked": True,
}

BLOCKED_SEMANTIC_FAMILY_EXPECTATIONS = {
    "source_dependent_values": BLOCKED_SEMANTIC_STATUS,
    "venue_api_values": BLOCKED_SEMANTIC_STATUS,
    "venue_semantics": BLOCKED_SEMANTIC_STATUS,
    "fundamental_facts": BLOCKED_SEMANTIC_STATUS,
    "fee_semantics": BLOCKED_SEMANTIC_STATUS,
    "tick_semantics": BLOCKED_SEMANTIC_STATUS,
    "rate_limit_semantics": BLOCKED_SEMANTIC_STATUS,
    "order_entry_semantics": BLOCKED_SEMANTIC_STATUS,
    "settlement_semantics": BLOCKED_SEMANTIC_STATUS,
    "private_state_semantics": BLOCKED_SEMANTIC_STATUS,
    "replay_semantics": BLOCKED_SEMANTIC_STATUS,
    "historical_data_semantics": BLOCKED_SEMANTIC_STATUS,
}

RUNTIME_BLOCK_CONTRACT_EXPECTATIONS = {
    "live_reachability_created": False,
    "runtime_resolver_snapshot_created": False,
    "replay_execution_claimed": False,
    "paper_execution_claimed": False,
    "blocker_reduction_claimed": False,
    "order_execution_authority_created": False,
    "private_state_fetch_created": False,
    "runtime_authority_created": False,
    "freeze_authority_created": False,
    "profit_evidence_created": False,
}

ATOMICROWS_AUTHORITY_STATE_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "bundle_authority_present": False,
    "hash_authority_present": False,
    "sha_authority_present": False,
    "row_record_authority_present": False,
    "completion_authority_present": False,
    "claims_4183_row_completion": False,
    "claimed_atomicrows_row_count": UNBOUND_ROW_COUNT,
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_execution_claimed",
    "source_acceptance_execution_claimed",
    "source_fact_acceptance_claimed",
    "accepted_source_evidence_packet_creation_claimed",
    "connector_binding_enabled",
    "connector_semantic_binding_claimed",
    "connector_semantic_value_population_enabled",
    "source_dependent_value_acceptance_enabled",
    "venue_api_fact_population_enabled",
    "venue_semantics_acceptance_enabled",
    "fundamental_fact_population_enabled",
    "fee_semantics_acceptance_enabled",
    "tick_semantics_acceptance_enabled",
    "rate_limit_semantics_acceptance_enabled",
    "order_entry_semantics_acceptance_enabled",
    "settlement_semantics_acceptance_enabled",
    "private_state_semantics_acceptance_enabled",
    "replay_semantics_acceptance_enabled",
    "historical_data_semantics_acceptance_enabled",
    "live_reachability_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "private_state_fetch_enabled",
    "runtime_enabled",
    "live_enabled",
    "blocker_reduction_enabled",
    "order_execution_authority_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "profit_evidence_enabled",
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_row_record_creation_enabled",
    "atomicrows_completion_claim_enabled",
    "sha_freeze_enabled",
}

AUDIT_NO_CLAIM_FLAGS = {
    "retrieves_sources",
    "accepts_source_facts",
    "creates_accepted_source_packets",
    "creates_accepted_source_evidence",
    "binds_connector_semantics",
    "populates_connector_semantic_values",
    "populates_venue_api_facts",
    "populates_fundamental_facts",
    "accepts_source_dependent_values",
    "accepts_fee_semantics",
    "accepts_tick_semantics",
    "accepts_rate_limit_semantics",
    "accepts_order_entry_semantics",
    "accepts_settlement_semantics",
    "accepts_private_state_semantics",
    "accepts_replay_semantics",
    "accepts_historical_data_semantics",
    "creates_live_reachability",
    "creates_runtime_resolver_snapshot",
    "executes_replay",
    "executes_paper",
    "fetches_private_state",
    "creates_runtime_authority",
    "creates_order_authority",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "reduces_blockers",
    "creates_profit_evidence",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "creates_atomicrows_row_records",
    "claims_atomicrows_completion",
    "claims_4183_row_completion",
    "creates_freeze_authority",
}

EXPECTED_SCHEMA_DEFS = {
    "source_fixture_no_claim_flags",
    "source_root_no_claim_flags",
    "source_evidence_gate_confirmation",
    "accepted_packet_schema_contract",
    "source_required_placeholder_contract",
    "connector_semantic_block_contract",
    "blocked_semantic_families",
    "runtime_block_contract",
    "atomicrows_authority_state",
    "forbidden_action_flags",
    "audit_no_claim_flags",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
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
    expected: set[str],
    label: str,
) -> list[str]:
    return _validate_const_schema(
        definition,
        expected={field: False for field in expected},
        label=label,
    )


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


def _validate_bool_map(value: dict[str, Any], expected: set[str], label: str) -> list[str]:
    return _validate_const_map(
        value,
        {field: False for field in expected},
        label,
    )


def _mapping(
    value: dict[str, Any],
    field: str,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
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


def _validate_schema(schema: dict[str, Any]) -> list[str]:
    failures = _validate_schema_object_contract(
        schema,
        expected_fields=ROOT_FIELDS,
        label="schema",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"schema.properties.{field} must be const {expected}")

    properties = _properties(schema)
    expected_refs = {
        "fixture_no_claim_flags": "#/$defs/source_fixture_no_claim_flags",
        "no_claim_flags": "#/$defs/source_root_no_claim_flags",
        "source_evidence_gate_confirmation": "#/$defs/source_evidence_gate_confirmation",
    }
    for field, expected_ref in sorted(expected_refs.items()):
        prop = properties.get(field, {})
        if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
            failures.append(f"schema.properties.{field} must reference {expected_ref}")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, EXPECTED_SCHEMA_DEFS, "schema.$defs"))

    def_expectations = {
        "accepted_packet_schema_contract": ACCEPTED_PACKET_SCHEMA_CONTRACT_EXPECTATIONS,
        "source_required_placeholder_contract": SOURCE_REQUIRED_PLACEHOLDER_EXPECTATIONS,
        "connector_semantic_block_contract": CONNECTOR_SEMANTIC_BLOCK_EXPECTATIONS,
        "blocked_semantic_families": BLOCKED_SEMANTIC_FAMILY_EXPECTATIONS,
        "runtime_block_contract": RUNTIME_BLOCK_CONTRACT_EXPECTATIONS,
        "atomicrows_authority_state": ATOMICROWS_AUTHORITY_STATE_EXPECTATIONS,
    }
    for def_name, expected in sorted(def_expectations.items()):
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

    bool_defs = {
        "source_fixture_no_claim_flags": SOURCE_FIXTURE_NO_CLAIM_FLAGS,
        "source_root_no_claim_flags": SOURCE_ROOT_NO_CLAIM_FLAGS,
        "forbidden_action_flags": FORBIDDEN_ACTION_FLAGS,
        "audit_no_claim_flags": AUDIT_NO_CLAIM_FLAGS,
    }
    for def_name, expected in sorted(bool_defs.items()):
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_bool_map_schema(
                    definition,
                    expected=expected,
                    label=f"schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"schema.$defs.{def_name} must be an object")

    gate = defs.get("source_evidence_gate_confirmation")
    if isinstance(gate, dict):
        failures.extend(
            _validate_schema_object_contract(
                gate,
                expected_fields=GATE_FIELDS,
                label="schema.$defs.source_evidence_gate_confirmation",
            )
        )
        for field, expected in sorted(GATE_CONST_EXPECTATIONS.items()):
            if _const_value(gate, field) != expected:
                failures.append(
                    "schema.$defs.source_evidence_gate_confirmation."
                    f"{field} must be const {expected}"
                )
        nested_refs = {
            "accepted_packet_schema_contract": "#/$defs/accepted_packet_schema_contract",
            "source_required_placeholder_contract": (
                "#/$defs/source_required_placeholder_contract"
            ),
            "connector_semantic_block_contract": (
                "#/$defs/connector_semantic_block_contract"
            ),
            "blocked_semantic_families": "#/$defs/blocked_semantic_families",
            "runtime_block_contract": "#/$defs/runtime_block_contract",
            "atomicrows_authority_state": "#/$defs/atomicrows_authority_state",
            "forbidden_action_flags": "#/$defs/forbidden_action_flags",
            "audit_no_claim_flags": "#/$defs/audit_no_claim_flags",
        }
        gate_props = _properties(gate)
        for field, expected_ref in sorted(nested_refs.items()):
            prop = gate_props.get(field, {})
            if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
                failures.append(
                    "schema.$defs.source_evidence_gate_confirmation."
                    f"{field} must reference {expected_ref}"
                )

        hook_prop = gate_props.get("validation_hook_ids", {})
        items = hook_prop.get("items", {}) if isinstance(hook_prop, dict) else {}
        if not isinstance(hook_prop, dict) or hook_prop.get("type") != "array":
            failures.append("schema gate validation_hook_ids must be an array")
        elif hook_prop.get("minItems") != 1 or hook_prop.get("maxItems") != 1:
            failures.append("schema gate validation_hook_ids must contain exactly one item")
        elif not isinstance(items, dict) or items.get("const") != AUDIT_HOOK_ID:
            failures.append("schema gate validation_hook_ids must contain the audit hook")
    else:
        failures.append("schema.$defs.source_evidence_gate_confirmation must be an object")

    examples = schema.get("examples")
    if not isinstance(examples, list) or not examples:
        failures.append("schema must include at least one synthetic static audit example")
    else:
        example = examples[0]
        if not isinstance(example, dict) or example.get("gate_authority_class") != (
            GATE_AUTHORITY_CLASS
        ):
            failures.append("schema example must preserve static audit authority")
    return failures


def _validate_atomicrows_authority_state(
    state: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _validate_const_map(
        state,
        ATOMICROWS_AUTHORITY_STATE_EXPECTATIONS,
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
            label="source-evidence gate confirmation",
        )
    )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        SOURCE_FIXTURE_NO_CLAIM_FLAGS
        | SOURCE_ROOT_NO_CLAIM_FLAGS
        | FORBIDDEN_ACTION_FLAGS
        | AUDIT_NO_CLAIM_FLAGS
        | {
            field
            for field, expected in ACCEPTED_PACKET_SCHEMA_CONTRACT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in SOURCE_REQUIRED_PLACEHOLDER_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in CONNECTOR_SEMANTIC_BLOCK_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in RUNTIME_BLOCK_CONTRACT_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in ATOMICROWS_AUTHORITY_STATE_EXPECTATIONS.items()
            if expected is False
        }
    )
    must_be_true = (
        {
            field
            for field, expected in ACCEPTED_PACKET_SCHEMA_CONTRACT_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in SOURCE_REQUIRED_PLACEHOLDER_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in CONNECTOR_SEMANTIC_BLOCK_EXPECTATIONS.items()
            if expected is True
        }
    )

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in BLOCKED_SEMANTIC_FAMILY_EXPECTATIONS and item != BLOCKED_SEMANTIC_STATUS:
            failures.append(f"{path} must be {BLOCKED_SEMANTIC_STATUS}")
        if key in {"gate_status", "confirmation_status"} and item != CONFIRMATION_STATUS:
            failures.append(f"{path} must be {CONFIRMATION_STATUS}")
        if key == "gate_authority_class" and item != GATE_AUTHORITY_CLASS:
            failures.append(f"{path} must be {GATE_AUTHORITY_CLASS}")
        if key == "claimed_atomicrows_row_count" and item != UNBOUND_ROW_COUNT:
            failures.append(f"{path} must be {UNBOUND_ROW_COUNT}")
        if isinstance(item, str):
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_source_evidence_gate_confirmation_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "source-evidence gate confirmation fixture",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(
                f"source-evidence gate confirmation fixture.{field} must be {expected}"
            )

    fixture_flags, fixture_flag_failures = _mapping(
        fixture,
        "fixture_no_claim_flags",
        "source-evidence gate confirmation fixture",
    )
    failures.extend(fixture_flag_failures)
    if fixture_flags is not None:
        failures.extend(
            _validate_bool_map(
                fixture_flags,
                SOURCE_FIXTURE_NO_CLAIM_FLAGS,
                "fixture_no_claim_flags",
            )
        )

    root_no_claims, root_no_claim_failures = _mapping(
        fixture,
        "no_claim_flags",
        "source-evidence gate confirmation fixture",
    )
    failures.extend(root_no_claim_failures)
    if root_no_claims is not None:
        failures.extend(
            _validate_bool_map(
                root_no_claims,
                SOURCE_ROOT_NO_CLAIM_FLAGS,
                "no_claim_flags",
            )
        )

    gate, gate_failures = _mapping(
        fixture,
        "source_evidence_gate_confirmation",
        "source-evidence gate confirmation fixture",
    )
    failures.extend(gate_failures)
    if gate is None:
        return failures

    failures.extend(
        _require_exact_fields(
            gate,
            GATE_FIELDS,
            "source_evidence_gate_confirmation",
        )
    )
    for field, expected in sorted(GATE_CONST_EXPECTATIONS.items()):
        if gate.get(field) != expected:
            failures.append(f"source_evidence_gate_confirmation.{field} must be {expected}")

    nested_const_maps = {
        "accepted_packet_schema_contract": ACCEPTED_PACKET_SCHEMA_CONTRACT_EXPECTATIONS,
        "source_required_placeholder_contract": SOURCE_REQUIRED_PLACEHOLDER_EXPECTATIONS,
        "connector_semantic_block_contract": CONNECTOR_SEMANTIC_BLOCK_EXPECTATIONS,
        "blocked_semantic_families": BLOCKED_SEMANTIC_FAMILY_EXPECTATIONS,
        "runtime_block_contract": RUNTIME_BLOCK_CONTRACT_EXPECTATIONS,
    }
    for field, expected in sorted(nested_const_maps.items()):
        value, value_failures = _mapping(gate, field, "source_evidence_gate_confirmation")
        failures.extend(value_failures)
        if value is not None:
            failures.extend(_validate_const_map(value, expected, field))

    atomicrows_state, atomicrows_failures = _mapping(
        gate,
        "atomicrows_authority_state",
        "source_evidence_gate_confirmation",
    )
    failures.extend(atomicrows_failures)
    if atomicrows_state is not None:
        failures.extend(
            _validate_atomicrows_authority_state(
                atomicrows_state,
                repo_root=repo_root,
            )
        )

    forbidden_actions, action_failures = _mapping(
        gate,
        "forbidden_action_flags",
        "source_evidence_gate_confirmation",
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

    audit_no_claims, audit_no_claim_failures = _mapping(
        gate,
        "audit_no_claim_flags",
        "source_evidence_gate_confirmation",
    )
    failures.extend(audit_no_claim_failures)
    if audit_no_claims is not None:
        failures.extend(
            _validate_bool_map(
                audit_no_claims,
                AUDIT_NO_CLAIM_FLAGS,
                "audit_no_claim_flags",
            )
        )

    hook_ids = gate.get("validation_hook_ids")
    if hook_ids != [AUDIT_HOOK_ID]:
        failures.append(
            "source_evidence_gate_confirmation.validation_hook_ids must contain only "
            f"{AUDIT_HOOK_ID}"
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
            validate_source_evidence_gate_confirmation_fixture(
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
