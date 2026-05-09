#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_STATIC_VALIDATION_OK"
FAILURE_MARKER = "CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_STATIC_VALIDATION_FAILED"

SCHEMA_AUTHORITY_CLASS = (
    "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_BINDING_AUTHORITY"
)
GATE_AUTHORITY_CLASS = (
    "STATIC_AUDIT_SCHEMA_ONLY_NOT_SOURCE_RETRIEVAL_NOT_CONNECTOR_BINDING"
)
SURFACE_KIND = "CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_STATIC"
SURFACE_VERSION = "PR35_CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_SCHEMA_V1"
VALIDATION_HOOK = "CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_STATIC_AUDIT"
PLACEHOLDER = "SOURCE_REQUIRED"
PACKET_REF = "schemas/source_evidence/source_evidence.schema.json#/$defs/accepted_source_packet"
NO_PACKET_REF = "SOURCE_REQUIRED_NO_ACCEPTED_TARGET_FIELD_PACKET"
BLOCKED_BINDING_STATE = "BLOCKED_PENDING_TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE"
UNBOUND = "UNBOUND"
NO_PACKET_COUNT = "NO_ACCEPTED_TARGET_FIELD_PACKETS"

CANONICAL_BUNDLE_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

TARGET_FIELDS = [
    "connector.semantic.connector_semantic_values",
    "connector.venue_api.venue_api_facts",
    "connector.fundamentals.fundamental_facts",
    "connector.fees.fee_semantics",
    "connector.market.tick_semantics",
    "connector.api.rate_limit_semantics",
    "connector.settlement.settlement_rules",
    "connector.order_entry.order_entry_fields",
    "connector.order_status.status_lifecycle",
    "connector.private_state.private_state_fields",
    "connector.private_state.account_fields",
    "connector.private_state.balance_fields",
    "connector.selection.market_selection",
    "connector.selection.contract_selection",
    "connector.selection.event_selection",
    "connector.selection.symbol_selection",
    "connector.selection.live_venue_selection",
    "connector.runtime.runtime_resolver_snapshot",
    "connector.execution.replay_paper_execution",
    "connector.cash.runtime_cash_value",
    "connector.order_authority.order_authority_fields",
]

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "surface_version",
    "mode",
    "execution",
    "validation_mode",
    "deterministic_output",
    "gate_authority",
    "prerequisite_receipts",
    "connector_target_fields",
    "connector_scaffold_records",
    "connector_capability_cards",
    "active_connector_capability_matrix",
    "source_required_placeholder_policy",
    "accepted_target_field_packet_policy",
    "implementation_import_policy",
    "connector_semantic_binding_policy",
    "network_policy",
    "live_connector_policy",
    "semantic_population_policy",
    "selection_policy",
    "runtime_policy",
    "execution_policy",
    "live_reachability_policy",
    "order_authority_policy",
    "runtime_cash_policy",
    "source_authority_policy",
    "atomicrows_authority_state",
    "claim_policy",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR35_CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_BLOCKED_FIXTURE",
    "fixture_version": "PR35_CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_BLOCKED_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_CONNECTOR_NOT_SOURCE_FACT"
    ),
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "surface_kind": SURFACE_KIND,
    "surface_version": SURFACE_VERSION,
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "validation_mode": "STATIC_SCHEMA_ONLY_NON_MUTATING_AUDIT",
    "deterministic_output": True,
}

GATE_AUTHORITY_EXPECTATIONS = {
    "static_audit_only": True,
    "schema_only": True,
    "non_mutating_validator": True,
    "connector_scaffold_contracts_only": True,
    "runtime_authority_created": False,
    "connector_binding_authority_created": False,
    "source_authority_created": False,
}

PREREQUISITE_RECEIPT_EXPECTATIONS = {
    "venue_neutral_prediction_adapter_gate_receipt_required": True,
    "venue_neutral_prediction_adapter_gate_receipt_status": "REQUIRED",
    "source_evidence_gate_confirmation_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_status": "REQUIRED",
    "stage1_packet_schema_gate_receipt_required": True,
    "stage1_packet_schema_gate_receipt_status": "REQUIRED",
    "prerequisite_receipts_create_runtime_authority": False,
    "prerequisite_receipts_create_source_authority": False,
    "prerequisite_receipts_create_connector_binding_authority": False,
}

SOURCE_REQUIRED_PLACEHOLDER_POLICY_EXPECTATIONS = {
    "source_required_value": PLACEHOLDER,
    "placeholder_value_must_be_source_required": True,
    "target_field_metadata_required": True,
    "accepted_target_field_packets_required_before_semantic_binding": True,
    "exact_target_field_packet_required": True,
    "target_field_packet_validation_required": True,
    "wildcard_or_venue_level_packet_unlock_allowed": False,
    "placeholder_weakening_allowed": False,
    "connector_semantic_value_replacement_allowed": False,
    "accepted_target_field_packets_present": False,
    "source_required_placeholders_preserved": True,
}

ACCEPTED_TARGET_FIELD_PACKET_POLICY_EXPECTATIONS = {
    "accepted_source_packet_schema_ref": PACKET_REF,
    "accepted_target_field_packets_exist": False,
    "accepted_target_field_packets_created": False,
    "accepted_source_packet_creation_allowed": False,
    "source_retrieval_claimed": False,
    "source_acceptance_claimed": False,
    "source_facts_accepted": False,
    "connector_binding_allowed_without_accepted_target_field_packet": False,
    "connector_binding_blocked_without_accepted_target_field_packet": True,
}

IMPLEMENTATION_IMPORT_POLICY_EXPECTATIONS = {
    "venue_sdk_import_reference": UNBOUND,
    "venue_api_module_reference": UNBOUND,
    "implementation_authority_reference": UNBOUND,
    "connector_runtime_module_reference": UNBOUND,
    "venue_sdk_import_allowed": False,
    "venue_api_module_import_allowed": False,
    "implementation_authority_created": False,
}

CONNECTOR_SEMANTIC_BINDING_POLICY_EXPECTATIONS = {
    "connector_semantic_binding_blocked": True,
    "connector_semantic_binding_allowed": False,
    "connector_semantic_values_populated": False,
    "venue_api_facts_populated": False,
    "fundamental_facts_populated": False,
    "source_dependent_values_populated": False,
    "accepted_target_field_packet_validation_required": True,
}

NETWORK_POLICY_EXPECTATIONS = {
    "network_io_created": False,
    "network_io_allowed": False,
    "http_client_created": False,
    "websocket_client_created": False,
    "live_api_call_allowed": False,
}

LIVE_CONNECTOR_POLICY_EXPECTATIONS = {
    "live_connector_client_created": False,
    "live_connector_client_creation_allowed": False,
    "live_connector_reference": UNBOUND,
    "client_factory_reference": UNBOUND,
}

SEMANTIC_POPULATION_POLICY_EXPECTATIONS = {
    "connector_semantic_values_populated": False,
    "venue_api_facts_populated": False,
    "venue_fundamental_facts_populated": False,
    "exact_fee_semantics_populated": False,
    "exact_tick_semantics_populated": False,
    "exact_rate_limit_semantics_populated": False,
    "exact_settlement_semantics_populated": False,
    "exact_order_entry_fields_populated": False,
    "exact_order_status_lifecycle_populated": False,
    "exact_private_state_semantics_populated": False,
    "exact_account_semantics_populated": False,
    "exact_balance_semantics_populated": False,
}

SELECTION_POLICY_EXPECTATIONS = {
    "exact_market_selection_claimed": False,
    "exact_contract_selection_claimed": False,
    "exact_event_selection_claimed": False,
    "exact_symbol_selection_claimed": False,
    "exact_live_venue_selection_claimed": False,
}

RUNTIME_POLICY_EXPECTATIONS = {
    "runtime_resolver_snapshot_created": False,
    "runtime_resolver_snapshot_creation_claimed": False,
    "runtime_resolver_snapshot_reference": UNBOUND,
}

EXECUTION_POLICY_EXPECTATIONS = {
    "replay_execution_claimed": False,
    "paper_execution_claimed": False,
    "runtime_replay_result_packet_created": False,
    "runtime_paper_result_packet_created": False,
}

LIVE_REACHABILITY_POLICY_EXPECTATIONS = {
    "live_reachability_created": False,
    "live_reachability_claimed": False,
}

ORDER_AUTHORITY_POLICY_EXPECTATIONS = {
    "order_authority_created": False,
    "order_execution_authority_created": False,
    "order_submission_enabled": False,
    "order_cancel_enabled": False,
    "order_reduce_enabled": False,
    "order_close_enabled": False,
}

RUNTIME_CASH_POLICY_EXPECTATIONS = {
    "runtime_cash_value_authority_created": False,
    "runtime_cash_value_claimed": False,
    "runtime_cash_fetch_allowed": False,
    "balance_fetch_allowed": False,
    "account_state_fetch_allowed": False,
}

SOURCE_AUTHORITY_POLICY_EXPECTATIONS = {
    "source_retrieval_claimed": False,
    "source_acceptance_claimed": False,
    "source_facts_accepted": False,
    "accepted_source_packet_created": False,
    "accepted_source_evidence_packet_created": False,
    "accepted_source_packet_reference": UNBOUND,
}

ATOMICROWS_STATE_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "atomicrows_bundle_creation_claimed": False,
    "atomicrows_hash_creation_claimed": False,
    "atomicrows_sha_authority_claimed": False,
    "atomicrows_row_creation_claimed": False,
    "atomicrows_completion_claimed": False,
    "claims_4183_row_completion": False,
    "freeze_authority_claimed": False,
}

CLAIM_POLICY_EXPECTATIONS = {
    "blocker_reduction_claimed": False,
    "profit_claim_created": False,
    "profit_evidence_created": False,
    "order_execution_authority_created": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "source_fact_acceptance_enabled",
    "accepted_source_packet_creation_enabled",
    "accepted_source_evidence_packet_creation_enabled",
    "connector_semantic_binding_enabled",
    "connector_semantic_value_population_enabled",
    "venue_api_fact_population_enabled",
    "fundamental_fact_population_enabled",
    "exact_fee_semantics_enabled",
    "exact_tick_semantics_enabled",
    "exact_rate_limit_semantics_enabled",
    "exact_settlement_semantics_enabled",
    "exact_order_entry_fields_enabled",
    "exact_order_status_lifecycle_enabled",
    "exact_private_state_semantics_enabled",
    "exact_account_semantics_enabled",
    "exact_balance_semantics_enabled",
    "exact_market_selection_enabled",
    "exact_contract_selection_enabled",
    "exact_event_selection_enabled",
    "exact_symbol_selection_enabled",
    "exact_live_venue_selection_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "runtime_replay_result_packet_creation_enabled",
    "runtime_paper_result_packet_creation_enabled",
    "live_reachability_enabled",
    "live_connector_client_creation_enabled",
    "network_io_enabled",
    "http_client_enabled",
    "websocket_client_enabled",
    "venue_sdk_import_enabled",
    "venue_api_module_import_enabled",
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "account_state_fetch_enabled",
    "runtime_cash_value_authority_enabled",
    "order_authority_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_sha_authority_enabled",
    "atomicrows_row_creation_enabled",
    "atomicrows_completion_claim_enabled",
    "freeze_authority_enabled",
    "blocker_reduction_enabled",
    "profit_claim_enabled",
    "profit_evidence_creation_enabled",
}

NO_CLAIM_FLAGS = {
    "claims_source_retrieval",
    "claims_source_acceptance",
    "claims_source_fact_acceptance",
    "creates_accepted_source_packets",
    "creates_accepted_source_evidence_packets",
    "binds_connector_semantics",
    "populates_connector_semantic_values",
    "populates_venue_api_facts",
    "populates_fundamental_facts",
    "encodes_exact_fee_semantics",
    "encodes_exact_tick_semantics",
    "encodes_exact_rate_limit_semantics",
    "encodes_exact_settlement_semantics",
    "encodes_exact_order_entry_fields",
    "encodes_exact_order_status_lifecycle",
    "encodes_exact_private_state_semantics",
    "encodes_exact_account_semantics",
    "encodes_exact_balance_semantics",
    "selects_exact_markets",
    "selects_exact_contracts",
    "selects_exact_events",
    "selects_exact_symbols",
    "selects_live_venues",
    "creates_runtime_resolver_snapshots",
    "executes_replay",
    "executes_paper",
    "creates_runtime_replay_result_packets",
    "creates_runtime_paper_result_packets",
    "creates_live_reachability",
    "creates_live_connector_client",
    "creates_network_io",
    "creates_http_client",
    "creates_websocket_client",
    "imports_venue_sdk",
    "imports_venue_api_module",
    "fetches_private_state",
    "fetches_balances",
    "fetches_account_state",
    "creates_runtime_cash_value_authority",
    "creates_order_authority",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "claims_atomicrows_sha_authority",
    "creates_atomicrows_rows",
    "creates_atomicrows_row_records",
    "claims_atomicrows_completion",
    "claims_4183_row_completion",
    "creates_freeze_authority",
    "claims_blocker_reduction",
    "creates_profit_claim",
    "creates_profit_evidence",
}

TARGET_FIELD_METADATA_FIELDS = {
    "target_field_path",
    "field_family",
    "dependency_class",
    "blocker_code",
    "accepted_source_packet_required",
    "accepted_source_packet_schema_ref",
    "target_field_specific_packet_required",
    "exact_target_field_packet_required",
    "placeholder_retention",
    "semantic_binding_state",
}

PLACEHOLDER_RECORD_FIELDS = {
    "placeholder_id",
    "target_field_path",
    "placeholder_value",
    "source_dependency_state",
    "target_field_metadata",
    "accepted_source_evidence_present",
    "accepted_source_packet_reference",
    "semantic_binding_allowed",
    "semantic_value_population_allowed",
}

SCAFFOLD_RECORD_FIELDS = {
    "record_type",
    "record_id",
    "scaffold_state",
    "connector_id",
    "connector_display_name",
    "implementation_reference",
    "live_connector_client_reference",
    "network_io_reference",
    "accepted_source_evidence_present",
    "semantic_binding_state",
    "runtime_state",
    "source_required_placeholder_policy",
    "no_claim_flags",
}

CAPABILITY_CARD_FIELDS = {
    "card_type",
    "card_id",
    "connector_id",
    "card_state",
    "scaffold_contract_state",
    "accepted_source_evidence_present",
    "accepted_target_field_packet_count",
    "source_required_placeholders",
    "semantic_binding_allowed",
    "runtime_enabled",
    "live_enabled",
    "network_io_enabled",
    "live_connector_client_created",
    "forbidden_action_flags",
    "no_claim_flags",
}

MATRIX_FIELDS = {
    "matrix_id",
    "matrix_state",
    "accepted_target_field_packets_present",
    "connector_semantic_binding_allowed",
    "source_required_placeholder_only",
    "rows",
}

MATRIX_ROW_FIELDS = {
    "row_id",
    "target_field_path",
    "capability_family",
    "placeholder_value",
    "semantic_value",
    "source_dependency_state",
    "target_field_metadata",
    "accepted_source_evidence_present",
    "accepted_source_packet_reference",
    "semantic_binding_allowed",
    "runtime_binding_allowed",
}

EXPECTED_SCHEMA_DEFS = {
    "target_field_path",
    "target_field_metadata",
    "source_required_placeholder_record",
    "connector_scaffold_record",
    "connector_capability_card",
    "active_connector_capability_matrix",
    "active_connector_capability_matrix_row",
    "gate_authority",
    "prerequisite_receipts",
    "source_required_placeholder_policy",
    "accepted_target_field_packet_policy",
    "implementation_import_policy",
    "connector_semantic_binding_policy",
    "network_policy",
    "live_connector_policy",
    "semantic_population_policy",
    "selection_policy",
    "runtime_policy",
    "execution_policy",
    "live_reachability_policy",
    "order_authority_policy",
    "runtime_cash_policy",
    "source_authority_policy",
    "atomicrows_authority_state",
    "claim_policy",
    "forbidden_action_flags",
    "no_claim_flags",
}

FORBIDDEN_ROW_RECORD_KEYS = {
    "row_records",
    "atomicrows_row_records",
    "atomic_row",
    "atomic_rows",
    "atomicrows_rows",
    "bundle_rows",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "http://",
    "https://",
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
    "import ",
    "from ",
    "requests.",
    "aiohttp",
    "httpx",
    "urllib",
    "websockets.",
    "websocketclient",
    "venue_sdk",
    "runtimeclient",
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


def _ref_value(definition: dict[str, Any], property_name: str) -> str | None:
    prop = _properties(definition).get(property_name, {})
    ref = prop.get("$ref") if isinstance(prop, dict) else None
    return ref if isinstance(ref, str) else None


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
        failures.extend(
            _require_exact_fields(properties, expected_fields, f"{label}.properties")
        )

    required = definition.get("required")
    if not isinstance(required, list):
        failures.append(f"{label}.required must be a list")
    else:
        required_fields = set(required)
        if len(required) != len(required_fields):
            failures.append(f"{label}.required must not contain duplicate fields")
        missing_required = sorted(expected_fields - required_fields)
        unexpected_required = sorted(required_fields - expected_fields)
        if missing_required:
            failures.append(f"{label} missing required fields: {', '.join(missing_required)}")
        if unexpected_required:
            failures.append(
                f"{label} has unexpected required fields: {', '.join(unexpected_required)}"
            )
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


def _validate_bool_map(value: dict[str, Any], fields: set[str], label: str) -> list[str]:
    return _validate_const_map(value, {field: False for field in fields}, label)


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


def _mapping(
    value: dict[str, Any],
    field: str,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _non_empty_list(
    value: dict[str, Any],
    field: str,
    label: str,
) -> tuple[list[Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, list) or not item:
        return None, [f"{label}.{field} must be a non-empty list"]
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


def _actual_atomicrows_presence(repo_root: pathlib.Path) -> tuple[bool, bool]:
    root = repo_root.resolve()
    bundle_path = _canonical_path(root, CANONICAL_BUNDLE_RELATIVE_PATH)
    sha_path = _canonical_path(root, CANONICAL_BUNDLE_SHA_RELATIVE_PATH)
    return bundle_path.exists(), sha_path.exists()


def _schema_refs() -> dict[str, str]:
    return {
        "gate_authority": "#/$defs/gate_authority",
        "prerequisite_receipts": "#/$defs/prerequisite_receipts",
        "connector_target_fields": "#/$defs/target_field_metadata",
        "connector_scaffold_records": "#/$defs/connector_scaffold_record",
        "connector_capability_cards": "#/$defs/connector_capability_card",
        "active_connector_capability_matrix": "#/$defs/active_connector_capability_matrix",
        "source_required_placeholder_policy": "#/$defs/source_required_placeholder_policy",
        "accepted_target_field_packet_policy": "#/$defs/accepted_target_field_packet_policy",
        "implementation_import_policy": "#/$defs/implementation_import_policy",
        "connector_semantic_binding_policy": "#/$defs/connector_semantic_binding_policy",
        "network_policy": "#/$defs/network_policy",
        "live_connector_policy": "#/$defs/live_connector_policy",
        "semantic_population_policy": "#/$defs/semantic_population_policy",
        "selection_policy": "#/$defs/selection_policy",
        "runtime_policy": "#/$defs/runtime_policy",
        "execution_policy": "#/$defs/execution_policy",
        "live_reachability_policy": "#/$defs/live_reachability_policy",
        "order_authority_policy": "#/$defs/order_authority_policy",
        "runtime_cash_policy": "#/$defs/runtime_cash_policy",
        "source_authority_policy": "#/$defs/source_authority_policy",
        "atomicrows_authority_state": "#/$defs/atomicrows_authority_state",
        "claim_policy": "#/$defs/claim_policy",
        "forbidden_action_flags": "#/$defs/forbidden_action_flags",
        "no_claim_flags": "#/$defs/no_claim_flags",
    }


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
    for field, expected_ref in sorted(_schema_refs().items()):
        prop = properties.get(field, {})
        if field in {
            "connector_target_fields",
            "connector_scaffold_records",
            "connector_capability_cards",
        }:
            items = prop.get("items", {}) if isinstance(prop, dict) else {}
            if (
                not isinstance(prop, dict)
                or prop.get("type") != "array"
                or prop.get("minItems") != 1
                or not isinstance(items, dict)
                or items.get("$ref") != expected_ref
            ):
                failures.append(f"schema.properties.{field} must be a non-empty array of {expected_ref}")
        else:
            if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
                failures.append(f"schema.properties.{field} must reference {expected_ref}")

    hook_prop = properties.get("validation_hook_ids", {})
    hook_items = hook_prop.get("items", {}) if isinstance(hook_prop, dict) else {}
    if (
        not isinstance(hook_prop, dict)
        or hook_prop.get("type") != "array"
        or hook_prop.get("minItems") != 1
        or hook_prop.get("maxItems") != 1
        or not isinstance(hook_items, dict)
        or hook_items.get("const") != VALIDATION_HOOK
    ):
        failures.append("schema.properties.validation_hook_ids must contain only the gate hook")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    failures.extend(_require_exact_fields(defs, EXPECTED_SCHEMA_DEFS, "schema.$defs"))

    target_def = defs.get("target_field_path")
    if not isinstance(target_def, dict) or target_def.get("enum") != TARGET_FIELDS:
        failures.append("schema.$defs.target_field_path must enumerate connector target fields")

    metadata_def = defs.get("target_field_metadata")
    if isinstance(metadata_def, dict):
        failures.extend(
            _validate_schema_object_contract(
                metadata_def,
                expected_fields=TARGET_FIELD_METADATA_FIELDS,
                label="schema.$defs.target_field_metadata",
            )
        )
        if _ref_value(metadata_def, "target_field_path") != "#/$defs/target_field_path":
            failures.append("target_field_metadata.target_field_path must reference target field path")
        if _const_value(metadata_def, "accepted_source_packet_required") is not True:
            failures.append("target_field_metadata.accepted_source_packet_required must be const true")
        if _const_value(metadata_def, "accepted_source_packet_schema_ref") != PACKET_REF:
            failures.append("target_field_metadata.accepted_source_packet_schema_ref must be accepted packet schema")
        if _const_value(metadata_def, "target_field_specific_packet_required") is not True:
            failures.append("target_field_metadata.target_field_specific_packet_required must be const true")
        if _const_value(metadata_def, "exact_target_field_packet_required") is not True:
            failures.append("target_field_metadata.exact_target_field_packet_required must be const true")
        if _const_value(metadata_def, "semantic_binding_state") != BLOCKED_BINDING_STATE:
            failures.append("target_field_metadata.semantic_binding_state must be blocked")
    else:
        failures.append("schema.$defs.target_field_metadata must be an object")

    for def_name, fields in [
        ("source_required_placeholder_record", PLACEHOLDER_RECORD_FIELDS),
        ("connector_scaffold_record", SCAFFOLD_RECORD_FIELDS),
        ("connector_capability_card", CAPABILITY_CARD_FIELDS),
        ("active_connector_capability_matrix", MATRIX_FIELDS),
        ("active_connector_capability_matrix_row", MATRIX_ROW_FIELDS),
    ]:
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_schema_object_contract(
                    definition,
                    expected_fields=fields,
                    label=f"schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"schema.$defs.{def_name} must be an object")

    policy_expectations = {
        "gate_authority": GATE_AUTHORITY_EXPECTATIONS,
        "prerequisite_receipts": PREREQUISITE_RECEIPT_EXPECTATIONS,
        "source_required_placeholder_policy": SOURCE_REQUIRED_PLACEHOLDER_POLICY_EXPECTATIONS,
        "accepted_target_field_packet_policy": ACCEPTED_TARGET_FIELD_PACKET_POLICY_EXPECTATIONS,
        "implementation_import_policy": IMPLEMENTATION_IMPORT_POLICY_EXPECTATIONS,
        "connector_semantic_binding_policy": CONNECTOR_SEMANTIC_BINDING_POLICY_EXPECTATIONS,
        "network_policy": NETWORK_POLICY_EXPECTATIONS,
        "live_connector_policy": LIVE_CONNECTOR_POLICY_EXPECTATIONS,
        "semantic_population_policy": SEMANTIC_POPULATION_POLICY_EXPECTATIONS,
        "selection_policy": SELECTION_POLICY_EXPECTATIONS,
        "runtime_policy": RUNTIME_POLICY_EXPECTATIONS,
        "execution_policy": EXECUTION_POLICY_EXPECTATIONS,
        "live_reachability_policy": LIVE_REACHABILITY_POLICY_EXPECTATIONS,
        "order_authority_policy": ORDER_AUTHORITY_POLICY_EXPECTATIONS,
        "runtime_cash_policy": RUNTIME_CASH_POLICY_EXPECTATIONS,
        "source_authority_policy": SOURCE_AUTHORITY_POLICY_EXPECTATIONS,
        "atomicrows_authority_state": ATOMICROWS_STATE_EXPECTATIONS,
        "claim_policy": CLAIM_POLICY_EXPECTATIONS,
    }
    for def_name, expected in sorted(policy_expectations.items()):
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
        "forbidden_action_flags": FORBIDDEN_ACTION_FLAGS,
        "no_claim_flags": NO_CLAIM_FLAGS,
    }
    for def_name, fields in sorted(bool_defs.items()):
        definition = defs.get(def_name)
        if isinstance(definition, dict):
            failures.extend(
                _validate_const_schema(
                    definition,
                    expected={field: False for field in fields},
                    label=f"schema.$defs.{def_name}",
                )
            )
        else:
            failures.append(f"schema.$defs.{def_name} must be an object")

    examples = schema.get("examples")
    if not isinstance(examples, list) or not examples:
        failures.append("schema must include a synthetic blocked example")
    else:
        example = examples[0]
        if not isinstance(example, dict) or example.get("schema_authority_class") != (
            SCHEMA_AUTHORITY_CLASS
        ):
            failures.append("schema example must preserve static schema authority")
    return failures


def _validate_target_field_metadata(metadata: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(metadata, TARGET_FIELD_METADATA_FIELDS, label)
    target_field_path = metadata.get("target_field_path")
    if target_field_path not in TARGET_FIELDS:
        failures.append(f"{label}.target_field_path must be an expected connector target field")
    if not isinstance(metadata.get("field_family"), str) or not metadata.get("field_family"):
        failures.append(f"{label}.field_family must be a non-empty string")
    expected_values = {
        "dependency_class": "TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE_REQUIRED",
        "blocker_code": "BLOCKER_CONNECTOR_TARGET_FIELD_SOURCE_REQUIRED",
        "accepted_source_packet_required": True,
        "accepted_source_packet_schema_ref": PACKET_REF,
        "target_field_specific_packet_required": True,
        "exact_target_field_packet_required": True,
        "placeholder_retention": "SOURCE_REQUIRED_UNTIL_ACCEPTED_TARGET_FIELD_PACKET",
        "semantic_binding_state": BLOCKED_BINDING_STATE,
    }
    for field, expected in expected_values.items():
        if metadata.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def _validate_placeholder_record(record: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(record, PLACEHOLDER_RECORD_FIELDS, label)
    if record.get("target_field_path") not in TARGET_FIELDS:
        failures.append(f"{label}.target_field_path must be an expected connector target field")
    if record.get("placeholder_value") != PLACEHOLDER:
        failures.append(f"{label}.placeholder_value must be {PLACEHOLDER}")
    if record.get("source_dependency_state") != "SOURCE_REQUIRED_PLACEHOLDER":
        failures.append(f"{label}.source_dependency_state must be SOURCE_REQUIRED_PLACEHOLDER")
    if record.get("accepted_source_evidence_present") is not False:
        failures.append(f"{label}.accepted_source_evidence_present must be false")
    if record.get("accepted_source_packet_reference") != NO_PACKET_REF:
        failures.append(f"{label}.accepted_source_packet_reference must be {NO_PACKET_REF}")
    if record.get("semantic_binding_allowed") is not False:
        failures.append(f"{label}.semantic_binding_allowed must be false")
    if record.get("semantic_value_population_allowed") is not False:
        failures.append(f"{label}.semantic_value_population_allowed must be false")
    metadata, metadata_failures = _mapping(record, "target_field_metadata", label)
    failures.extend(metadata_failures)
    if metadata is not None:
        failures.extend(_validate_target_field_metadata(metadata, f"{label}.target_field_metadata"))
        if metadata.get("target_field_path") != record.get("target_field_path"):
            failures.append(f"{label}.target_field_metadata.target_field_path must match record target")
    return failures


def _validate_target_field_metadata_list(records: Any, label: str) -> list[str]:
    if not isinstance(records, list) or not records:
        return [f"{label} must be a non-empty list"]
    failures: list[str] = []
    seen: list[str] = []
    for index, record in enumerate(records):
        item_label = f"{label}[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{item_label} must be an object")
            continue
        failures.extend(_validate_target_field_metadata(record, item_label))
        target = record.get("target_field_path")
        if isinstance(target, str):
            seen.append(target)
    if seen != TARGET_FIELDS:
        failures.append(f"{label} must preserve the expected connector target field order")
    return failures


def _validate_placeholder_records(records: Any, label: str) -> list[str]:
    if not isinstance(records, list) or not records:
        return [f"{label} must be a non-empty list"]
    failures: list[str] = []
    seen: list[str] = []
    for index, record in enumerate(records):
        item_label = f"{label}[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{item_label} must be an object")
            continue
        failures.extend(_validate_placeholder_record(record, item_label))
        target = record.get("target_field_path")
        if isinstance(target, str):
            seen.append(target)
    if seen != TARGET_FIELDS:
        failures.append(f"{label} must contain SOURCE_REQUIRED placeholders for every connector target field")
    return failures


def _validate_scaffold_records(records: Any) -> list[str]:
    if not isinstance(records, list) or not records:
        return ["connector_scaffold_records must be a non-empty list"]
    failures: list[str] = []
    for index, record in enumerate(records):
        label = f"connector_scaffold_records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(record, SCAFFOLD_RECORD_FIELDS, label))
        expected = {
            "record_type": "CONNECTOR_SCAFFOLD_RECORD_SOURCE_REQUIRED_PLACEHOLDER",
            "scaffold_state": "PLACEHOLDER_ONLY_NOT_RUNTIME_CONNECTOR",
            "connector_id": PLACEHOLDER,
            "connector_display_name": PLACEHOLDER,
            "implementation_reference": UNBOUND,
            "live_connector_client_reference": UNBOUND,
            "network_io_reference": UNBOUND,
            "accepted_source_evidence_present": False,
            "semantic_binding_state": BLOCKED_BINDING_STATE,
            "runtime_state": "DISABLED",
        }
        for field, expected_value in sorted(expected.items()):
            if record.get(field) != expected_value:
                failures.append(f"{label}.{field} must be {expected_value}")
        policy, policy_failures = _mapping(record, "source_required_placeholder_policy", label)
        failures.extend(policy_failures)
        if policy is not None:
            failures.extend(
                _validate_const_map(
                    policy,
                    SOURCE_REQUIRED_PLACEHOLDER_POLICY_EXPECTATIONS,
                    f"{label}.source_required_placeholder_policy",
                )
            )
        no_claims, no_claim_failures = _mapping(record, "no_claim_flags", label)
        failures.extend(no_claim_failures)
        if no_claims is not None:
            failures.extend(_validate_bool_map(no_claims, NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    return failures


def _validate_capability_cards(cards: Any) -> list[str]:
    if not isinstance(cards, list) or not cards:
        return ["connector_capability_cards must be a non-empty list"]
    failures: list[str] = []
    for index, card in enumerate(cards):
        label = f"connector_capability_cards[{index}]"
        if not isinstance(card, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(card, CAPABILITY_CARD_FIELDS, label))
        expected = {
            "card_type": "CONNECTOR_CAPABILITY_CARD_SOURCE_REQUIRED_SCAFFOLD",
            "connector_id": PLACEHOLDER,
            "card_state": "SOURCE_REQUIRED_PLACEHOLDER_ONLY",
            "scaffold_contract_state": "CONTRACT_ONLY_NOT_RUNTIME_CONNECTOR",
            "accepted_source_evidence_present": False,
            "accepted_target_field_packet_count": NO_PACKET_COUNT,
            "semantic_binding_allowed": False,
            "runtime_enabled": False,
            "live_enabled": False,
            "network_io_enabled": False,
            "live_connector_client_created": False,
        }
        for field, expected_value in sorted(expected.items()):
            if card.get(field) != expected_value:
                failures.append(f"{label}.{field} must be {expected_value}")
        failures.extend(
            _validate_placeholder_records(
                card.get("source_required_placeholders"),
                f"{label}.source_required_placeholders",
            )
        )
        actions, action_failures = _mapping(card, "forbidden_action_flags", label)
        failures.extend(action_failures)
        if actions is not None:
            failures.extend(_validate_bool_map(actions, FORBIDDEN_ACTION_FLAGS, f"{label}.forbidden_action_flags"))
        no_claims, no_claim_failures = _mapping(card, "no_claim_flags", label)
        failures.extend(no_claim_failures)
        if no_claims is not None:
            failures.extend(_validate_bool_map(no_claims, NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    return failures


def _validate_active_matrix(matrix: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(matrix, MATRIX_FIELDS, "active_connector_capability_matrix")
    expected = {
        "matrix_state": "SOURCE_REQUIRED_PLACEHOLDER_ONLY",
        "accepted_target_field_packets_present": False,
        "connector_semantic_binding_allowed": False,
        "source_required_placeholder_only": True,
    }
    for field, expected_value in sorted(expected.items()):
        if matrix.get(field) != expected_value:
            failures.append(f"active_connector_capability_matrix.{field} must be {expected_value}")
    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        return failures + ["active_connector_capability_matrix.rows must be a non-empty list"]
    seen: list[str] = []
    for index, row in enumerate(rows):
        label = f"active_connector_capability_matrix.rows[{index}]"
        if not isinstance(row, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(row, MATRIX_ROW_FIELDS, label))
        if row.get("target_field_path") not in TARGET_FIELDS:
            failures.append(f"{label}.target_field_path must be an expected connector target field")
        if isinstance(row.get("target_field_path"), str):
            seen.append(row["target_field_path"])
        for field in ["placeholder_value", "semantic_value"]:
            if row.get(field) != PLACEHOLDER:
                failures.append(f"{label}.{field} must be {PLACEHOLDER}")
        expected_row = {
            "source_dependency_state": "SOURCE_REQUIRED_PLACEHOLDER",
            "accepted_source_evidence_present": False,
            "accepted_source_packet_reference": NO_PACKET_REF,
            "semantic_binding_allowed": False,
            "runtime_binding_allowed": False,
        }
        for field, expected_value in sorted(expected_row.items()):
            if row.get(field) != expected_value:
                failures.append(f"{label}.{field} must be {expected_value}")
        metadata, metadata_failures = _mapping(row, "target_field_metadata", label)
        failures.extend(metadata_failures)
        if metadata is not None:
            failures.extend(_validate_target_field_metadata(metadata, f"{label}.target_field_metadata"))
            if metadata.get("target_field_path") != row.get("target_field_path"):
                failures.append(f"{label}.target_field_metadata.target_field_path must match row target")
    if seen != TARGET_FIELDS:
        failures.append(
            "active_connector_capability_matrix.rows must preserve SOURCE_REQUIRED rows for every connector target field"
        )
    return failures


def _validate_atomicrows_state(
    state: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _validate_const_map(
        state,
        ATOMICROWS_STATE_EXPECTATIONS,
        "atomicrows_authority_state",
    )
    bundle_present, sha_present = _actual_atomicrows_presence(repo_root)
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
    if bundle_present:
        failures.append(
            "canonical AtomicRows bundle must remain absent during connector scaffold "
            f"source-required gate validation: {CANONICAL_BUNDLE_RELATIVE_PATH}"
        )
    if sha_present:
        failures.append(
            "canonical AtomicRows bundle hash must remain absent during connector "
            f"scaffold source-required gate validation: {CANONICAL_BUNDLE_SHA_RELATIVE_PATH}"
        )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expectation_maps = [
        GATE_AUTHORITY_EXPECTATIONS,
        PREREQUISITE_RECEIPT_EXPECTATIONS,
        SOURCE_REQUIRED_PLACEHOLDER_POLICY_EXPECTATIONS,
        ACCEPTED_TARGET_FIELD_PACKET_POLICY_EXPECTATIONS,
        IMPLEMENTATION_IMPORT_POLICY_EXPECTATIONS,
        CONNECTOR_SEMANTIC_BINDING_POLICY_EXPECTATIONS,
        NETWORK_POLICY_EXPECTATIONS,
        LIVE_CONNECTOR_POLICY_EXPECTATIONS,
        SEMANTIC_POPULATION_POLICY_EXPECTATIONS,
        SELECTION_POLICY_EXPECTATIONS,
        RUNTIME_POLICY_EXPECTATIONS,
        EXECUTION_POLICY_EXPECTATIONS,
        LIVE_REACHABILITY_POLICY_EXPECTATIONS,
        ORDER_AUTHORITY_POLICY_EXPECTATIONS,
        RUNTIME_CASH_POLICY_EXPECTATIONS,
        SOURCE_AUTHORITY_POLICY_EXPECTATIONS,
        ATOMICROWS_STATE_EXPECTATIONS,
        CLAIM_POLICY_EXPECTATIONS,
    ]
    must_be_false = (
        FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_FLAGS
        | {field for expected in expectation_maps for field, value in expected.items() if value is False}
        | {
            "accepted_source_evidence_present",
            "accepted_target_field_packets_present",
            "semantic_binding_allowed",
            "runtime_binding_allowed",
            "semantic_value_population_allowed",
            "runtime_enabled",
            "live_enabled",
            "network_io_enabled",
            "live_connector_client_created",
        }
    )
    must_be_true = {
        field for expected in expectation_maps for field, value in expected.items() if value is True
    } | {"source_required_placeholder_only"}

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain AtomicRows row records")
        if key in {"placeholder_value", "semantic_value", "connector_id", "connector_display_name"} and item != PLACEHOLDER:
            failures.append(f"{path} must remain {PLACEHOLDER}")
        if key.endswith("_reference") and key not in {"accepted_source_packet_reference"} and item != UNBOUND:
            failures.append(f"{path} must remain {UNBOUND}")
        if key == "accepted_source_packet_reference" and item not in {NO_PACKET_REF, UNBOUND}:
            failures.append(f"{path} must remain unbound without an accepted target-field packet")
        if key == "accepted_target_field_packet_count" and item != NO_PACKET_COUNT:
            failures.append(f"{path} must be {NO_PACKET_COUNT}")
        if isinstance(item, str):
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private implementation fragment: {fragment}"
                    )
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime or venue values")
    return failures


def validate_connector_scaffold_source_required_gate_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "connector scaffold source-required gate fixture",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(
                f"connector scaffold source-required gate fixture.{field} must be {expected}"
            )

    map_expectations = {
        "gate_authority": GATE_AUTHORITY_EXPECTATIONS,
        "prerequisite_receipts": PREREQUISITE_RECEIPT_EXPECTATIONS,
        "source_required_placeholder_policy": SOURCE_REQUIRED_PLACEHOLDER_POLICY_EXPECTATIONS,
        "accepted_target_field_packet_policy": ACCEPTED_TARGET_FIELD_PACKET_POLICY_EXPECTATIONS,
        "implementation_import_policy": IMPLEMENTATION_IMPORT_POLICY_EXPECTATIONS,
        "connector_semantic_binding_policy": CONNECTOR_SEMANTIC_BINDING_POLICY_EXPECTATIONS,
        "network_policy": NETWORK_POLICY_EXPECTATIONS,
        "live_connector_policy": LIVE_CONNECTOR_POLICY_EXPECTATIONS,
        "semantic_population_policy": SEMANTIC_POPULATION_POLICY_EXPECTATIONS,
        "selection_policy": SELECTION_POLICY_EXPECTATIONS,
        "runtime_policy": RUNTIME_POLICY_EXPECTATIONS,
        "execution_policy": EXECUTION_POLICY_EXPECTATIONS,
        "live_reachability_policy": LIVE_REACHABILITY_POLICY_EXPECTATIONS,
        "order_authority_policy": ORDER_AUTHORITY_POLICY_EXPECTATIONS,
        "runtime_cash_policy": RUNTIME_CASH_POLICY_EXPECTATIONS,
        "source_authority_policy": SOURCE_AUTHORITY_POLICY_EXPECTATIONS,
        "claim_policy": CLAIM_POLICY_EXPECTATIONS,
    }
    for field, expectations in sorted(map_expectations.items()):
        value, map_failures = _mapping(
            fixture,
            field,
            "connector scaffold source-required gate fixture",
        )
        failures.extend(map_failures)
        if value is not None:
            failures.extend(_validate_const_map(value, expectations, field))

    failures.extend(
        _validate_target_field_metadata_list(
            fixture.get("connector_target_fields"),
            "connector_target_fields",
        )
    )
    failures.extend(_validate_scaffold_records(fixture.get("connector_scaffold_records")))
    failures.extend(_validate_capability_cards(fixture.get("connector_capability_cards")))

    matrix, matrix_failures = _mapping(
        fixture,
        "active_connector_capability_matrix",
        "connector scaffold source-required gate fixture",
    )
    failures.extend(matrix_failures)
    if matrix is not None:
        failures.extend(_validate_active_matrix(matrix))

    atomicrows, atomicrows_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "connector scaffold source-required gate fixture",
    )
    failures.extend(atomicrows_failures)
    if atomicrows is not None:
        failures.extend(_validate_atomicrows_state(atomicrows, repo_root=repo_root))

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "connector scaffold source-required gate fixture",
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
        "connector scaffold source-required gate fixture",
    )
    failures.extend(no_claim_failures)
    if no_claims is not None:
        failures.extend(_validate_bool_map(no_claims, NO_CLAIM_FLAGS, "no_claim_flags"))

    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")

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
            validate_connector_scaffold_source_required_gate_fixture(
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
