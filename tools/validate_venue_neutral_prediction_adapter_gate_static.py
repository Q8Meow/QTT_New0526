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

SUCCESS_MARKER = "VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_STATIC_VALIDATION_OK"
FAILURE_MARKER = "VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_STATIC_VALIDATION_FAILED"

SCHEMA_AUTHORITY_CLASS = "VENUE_NEUTRAL_PREDICTION_ADAPTER_SCHEMA_ONLY_STATIC_AUDIT"
RECORD_AUTHORITY_CLASS = "VENUE_NEUTRAL_ABSTRACT_RECORD_NOT_RUNTIME_AUTHORITY"
ADAPTER_GATE_AUTHORITY_CLASS = "SCHEMA_ONLY_STATIC_AUDIT_NOT_RUNTIME_AUTHORITY"
SURFACE_VERSION = "PR34_VENUE_NEUTRAL_PREDICTION_ADAPTER_SCHEMA_V1"
VALIDATION_HOOK = "VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_STATIC_AUDIT"

ALLOWED_SOURCE_DEPENDENCY_STATES = [
    "SOURCE_REQUIRED_PLACEHOLDER",
    "OWNER_POLICY_REQUIRED",
    "RUNTIME_OBSERVATION_REQUIRED",
    "ACCEPTED_SOURCE_PACKET_BOUND",
    "NOT_APPLICABLE",
]

EXPECTED_ADAPTER_SURFACES = [
    "VenueNeutralMarketSnapshot",
    "VenueNeutralOrderIntent",
    "VenueNeutralOrderValidationRequest",
    "VenueNeutralOrderValidationResult",
    "VenueNeutralPrivateStateRequest",
    "VenueNeutralPrivateStatePlaceholder",
    "VenueNeutralMarketDataPlaceholder",
    "VenueNeutralExecutionCapabilityPlaceholder",
    "VenueNeutralResolverInputRef",
    "VenueNeutralAdapterGateReport",
]

EXPECTED_SCHEMA_FILES = {
    "VenueNeutralMarketSnapshot": "venue_neutral_market_snapshot.schema.json",
    "VenueNeutralOrderIntent": "venue_neutral_order_intent.schema.json",
    "VenueNeutralOrderValidationRequest": (
        "venue_neutral_order_validation_request.schema.json"
    ),
    "VenueNeutralOrderValidationResult": (
        "venue_neutral_order_validation_result.schema.json"
    ),
    "VenueNeutralPrivateStateRequest": "venue_neutral_private_state_request.schema.json",
    "VenueNeutralPrivateStatePlaceholder": (
        "venue_neutral_private_state_placeholder.schema.json"
    ),
    "VenueNeutralMarketDataPlaceholder": (
        "venue_neutral_market_data_placeholder.schema.json"
    ),
    "VenueNeutralExecutionCapabilityPlaceholder": (
        "venue_neutral_execution_capability_placeholder.schema.json"
    ),
    "VenueNeutralResolverInputRef": "venue_neutral_resolver_input_ref.schema.json",
    "VenueNeutralAdapterGateReport": "venue_neutral_adapter_gate_report.schema.json",
}

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
    "validation_mode",
    "deterministic_output",
    "adapter_gate_authority",
    "expected_adapter_surfaces",
    "adapter_schema_contracts",
    "prerequisite_receipts",
    "source_dependency_policy",
    "placeholder_records",
    "connector_scaffold_policy",
    "connector_semantic_policy",
    "selection_policy",
    "runtime_policy",
    "execution_policy",
    "live_reachability_policy",
    "order_authority_policy",
    "source_authority_policy",
    "atomicrows_authority_state",
    "claim_policy",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_PR34_VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_BLOCKED_FIXTURE"
    ),
    "fixture_version": "PR34_VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_BLOCKED_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ADAPTER_RUNTIME_AUTHORITY_NOT_SOURCE_FACT"
    ),
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "surface_kind": "VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "validation_mode": "STATIC_SCHEMA_ONLY_NON_MUTATING_AUDIT",
    "deterministic_output": True,
}

SCHEMA_FIELDS = {
    "surface_name",
    "surface_version",
    "schema_authority_class",
    "record_authority_class",
    "adapter_gate_authority_class",
    "mode",
    "execution",
    "static_audit_only",
    "schema_only",
    "abstract_internal_fields_only",
    "runtime_authority_allowed",
    "connector_scaffold_allowed",
    "connector_semantic_value_population_allowed",
    "venue_specific_semantic_values_allowed",
    "exact_selection_allowed",
    "source_dependency_state",
    "internal_reference",
    "abstract_payload_fields",
    "source_required_placeholders",
}

SCHEMA_CONST_EXPECTATIONS = {
    "surface_version": SURFACE_VERSION,
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "record_authority_class": RECORD_AUTHORITY_CLASS,
    "adapter_gate_authority_class": ADAPTER_GATE_AUTHORITY_CLASS,
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "static_audit_only": True,
    "schema_only": True,
    "abstract_internal_fields_only": True,
    "runtime_authority_allowed": False,
    "connector_scaffold_allowed": False,
    "connector_semantic_value_population_allowed": False,
    "venue_specific_semantic_values_allowed": False,
    "exact_selection_allowed": False,
}

PLACEHOLDER_FIELDS = {
    "placeholder_type",
    "target_field_path",
    "dependency_class",
    "blocker_code",
    "acceptance_route",
    "source_dependency_state",
}

CONTRACT_FIELDS = {
    "surface_name",
    "schema_path",
    "schema_exists_required",
    "schema_only",
    "static_audit_only",
    "abstract_internal_fields_only",
    "source_dependency_state_allowed_values",
    "source_required_placeholder_metadata_required",
    "connector_scaffold_created",
    "connector_semantic_values_populated",
    "exact_selection_claimed",
    "runtime_authority_allowed",
    "live_reachability_claimed",
    "order_authority_claimed",
    "blocker_reduction_claimed",
    "profit_claimed",
    "atomicrows_authority_claimed",
}

CONTRACT_FLAG_EXPECTATIONS = {
    "schema_exists_required": True,
    "schema_only": True,
    "static_audit_only": True,
    "abstract_internal_fields_only": True,
    "source_required_placeholder_metadata_required": True,
    "connector_scaffold_created": False,
    "connector_semantic_values_populated": False,
    "exact_selection_claimed": False,
    "runtime_authority_allowed": False,
    "live_reachability_claimed": False,
    "order_authority_claimed": False,
    "blocker_reduction_claimed": False,
    "profit_claimed": False,
    "atomicrows_authority_claimed": False,
}

ADAPTER_GATE_AUTHORITY_EXPECTATIONS = {
    "schema_only_static_audit": True,
    "static_validation_only": True,
    "non_mutating_validator": True,
    "abstract_internal_records_only": True,
    "runtime_authority_created": False,
    "runtime_authority_allowed": False,
}

PREREQUISITE_RECEIPT_FIELDS = {
    "stage1_packet_schema_gate_receipt_required",
    "stage1_packet_schema_gate_receipt_status",
    "source_evidence_gate_confirmation_receipt_required",
    "source_evidence_gate_confirmation_receipt_status",
    "backbone_manifest_receipt_required",
    "backbone_manifest_receipt_status",
    "backbone_manifest_runtime_authority_created",
    "prerequisite_receipts_create_runtime_authority",
}

PREREQUISITE_RECEIPT_EXPECTATIONS = {
    "stage1_packet_schema_gate_receipt_required": True,
    "stage1_packet_schema_gate_receipt_status": "REQUIRED",
    "source_evidence_gate_confirmation_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_status": "REQUIRED",
    "backbone_manifest_receipt_required": True,
    "backbone_manifest_runtime_authority_created": False,
    "prerequisite_receipts_create_runtime_authority": False,
}

SOURCE_DEPENDENCY_POLICY_EXPECTATIONS = {
    "source_required_placeholders_require_target_field_path": True,
    "source_required_placeholders_require_dependency_class": True,
    "source_required_placeholders_require_blocker_code": True,
    "source_required_placeholders_require_acceptance_route": True,
    "source_retrieval_claimed": False,
    "source_fact_acceptance_claimed": False,
    "accepted_source_packet_created": False,
    "accepted_source_evidence_packet_created": False,
}

SOURCE_DEPENDENCY_POLICY_FIELDS = set(SOURCE_DEPENDENCY_POLICY_EXPECTATIONS) | {
    "allowed_source_dependency_states",
}

CONNECTOR_SCAFFOLD_POLICY_EXPECTATIONS = {
    "connector_scaffold_created": False,
    "connector_scaffold_creation_allowed": False,
    "connector_scaffolds_blocked_before_adapter_gate_green": True,
    "connector_imports_allowed": False,
    "venue_specific_connector_module_reference": "UNBOUND",
    "implementation_reference": "UNBOUND",
}

CONNECTOR_SEMANTIC_POLICY_EXPECTATIONS = {
    "connector_semantic_implementation_created": False,
    "connector_semantic_values_populated": False,
    "venue_specific_api_shape_populated": False,
    "endpoint_semantic_value_populated": False,
    "authentication_flow_semantic_value_populated": False,
    "fee_semantic_value_populated": False,
    "tick_semantic_value_populated": False,
    "rate_limit_semantic_value_populated": False,
    "settlement_semantic_value_populated": False,
    "order_status_semantic_value_populated": False,
    "private_state_semantic_value_populated": False,
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
    "runtime_resolver_snapshot_reference": "UNBOUND",
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

SOURCE_AUTHORITY_POLICY_EXPECTATIONS = {
    "source_retrieval_claimed": False,
    "source_acceptance_claimed": False,
    "source_facts_accepted": False,
    "accepted_source_packet_created": False,
    "accepted_source_evidence_packet_created": False,
    "accepted_source_packet_reference": "UNBOUND",
}

ATOMICROWS_STATE_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": True,
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
    "accepted_source_packet_creation_enabled",
    "accepted_source_evidence_packet_creation_enabled",
    "connector_scaffold_creation_enabled",
    "connector_import_enabled",
    "connector_semantic_implementation_enabled",
    "connector_semantic_value_population_enabled",
    "venue_specific_api_shape_enabled",
    "endpoint_semantic_value_enabled",
    "authentication_flow_semantic_value_enabled",
    "fee_semantic_value_enabled",
    "tick_semantic_value_enabled",
    "rate_limit_semantic_value_enabled",
    "settlement_semantic_value_enabled",
    "order_status_semantic_value_enabled",
    "private_state_semantic_value_enabled",
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
    "order_authority_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "order_execution_enabled",
    "source_fact_acceptance_enabled",
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
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "account_state_fetch_enabled",
}

NO_CLAIM_FLAGS = {
    "claims_source_retrieval",
    "claims_source_fact_acceptance",
    "creates_accepted_source_packets",
    "creates_accepted_source_evidence_packets",
    "creates_connector_scaffold",
    "imports_venue_specific_connector_module",
    "creates_connector_semantic_implementation",
    "populates_connector_semantic_values",
    "encodes_venue_specific_api_shape",
    "encodes_endpoint_semantic_value",
    "encodes_authentication_flow_semantic_value",
    "encodes_fee_semantic_value",
    "encodes_tick_semantic_value",
    "encodes_rate_limit_semantic_value",
    "encodes_settlement_semantic_value",
    "encodes_order_status_semantic_value",
    "encodes_private_state_semantic_value",
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
    "creates_order_authority",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "fetches_private_state",
    "fetches_balances",
    "fetches_account_state",
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
    "creates_profit_evidence",
    "creates_profit_claim",
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
    "connectors.",
    ".connectors",
    "import ",
    "endpoint:",
    "auth_flow",
    "authentication_flow:",
    "fee_value",
    "tick_value",
    "rate_limit_value",
    "settlement_value",
    "order_status_value",
    "exact_contract",
    "exact_event",
    "exact_market",
    "live_venue",
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


def _mapping(
    value: dict[str, Any], field: str, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _non_empty_list(
    value: dict[str, Any], field: str, label: str
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


def _validate_schema_file_set(schema_dir: pathlib.Path) -> list[str]:
    if not schema_dir.is_dir():
        return [f"schema directory is missing: {schema_dir}"]

    observed = sorted(path.name for path in schema_dir.glob("*.schema.json"))
    expected = sorted(EXPECTED_SCHEMA_FILES.values())
    failures: list[str] = []
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    if missing:
        failures.append(
            "venue-neutral adapter schema directory missing schema files: "
            + ", ".join(missing)
        )
    if extra:
        failures.append(
            "venue-neutral adapter schema directory has unexpected schema files: "
            + ", ".join(extra)
        )
    return failures


def _validate_placeholder_definition(
    definition: dict[str, Any],
    *,
    schema_name: str,
) -> list[str]:
    failures: list[str] = []
    if definition.get("type") != "object":
        failures.append(f"{schema_name} source_required_placeholder.type must be object")
    if definition.get("additionalProperties") is not False:
        failures.append(
            f"{schema_name} source_required_placeholder.additionalProperties must be false"
        )
    properties = _properties(definition)
    required = _required(definition)
    failures.extend(
        _require_exact_fields(
            properties,
            PLACEHOLDER_FIELDS,
            f"{schema_name} source_required_placeholder.properties",
        )
    )
    if required != PLACEHOLDER_FIELDS:
        failures.append(
            f"{schema_name} source_required_placeholder must require target metadata"
        )
    if _const_value(definition, "placeholder_type") != "SOURCE_REQUIRED_PLACEHOLDER":
        failures.append(
            f"{schema_name} source_required_placeholder.placeholder_type must be const"
        )
    if _ref_value(definition, "target_field_path") != "#/$defs/target_field_path":
        failures.append(
            f"{schema_name} source_required_placeholder.target_field_path must reference target path"
        )
    if _ref_value(definition, "source_dependency_state") != "#/$defs/source_dependency_state":
        failures.append(
            f"{schema_name} source_required_placeholder.source_dependency_state must reference allowed states"
        )
    return failures


def _validate_schema_contract(
    schema: dict[str, Any],
    *,
    surface_name: str,
    schema_path: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    expected_id = (
        "https://qtt.local/schemas/venue_neutral_prediction_adapter/"
        f"{schema_path.name}"
    )
    if schema.get("$id") != expected_id:
        failures.append(f"{schema_path.name}.$id must be {expected_id}")
    if schema.get("type") != "object":
        failures.append(f"{schema_path.name}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path.name}.additionalProperties must be false")

    properties = _properties(schema)
    required = _required(schema)
    failures.extend(_require_exact_fields(properties, SCHEMA_FIELDS, f"{schema_path.name}.properties"))
    if required != SCHEMA_FIELDS:
        missing = sorted(SCHEMA_FIELDS - required)
        unexpected = sorted(required - SCHEMA_FIELDS)
        if missing:
            failures.append(f"{schema_path.name} missing required fields: {', '.join(missing)}")
        if unexpected:
            failures.append(
                f"{schema_path.name} has unexpected required fields: {', '.join(unexpected)}"
            )

    if _const_value(schema, "surface_name") != surface_name:
        failures.append(f"{schema_path.name}.surface_name must be const {surface_name}")
    for field, expected_value in sorted(SCHEMA_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected_value:
            failures.append(f"{schema_path.name}.{field} must be const {expected_value}")

    if _ref_value(schema, "source_dependency_state") != "#/$defs/source_dependency_state":
        failures.append(f"{schema_path.name}.source_dependency_state must reference allowed states")
    if _ref_value(schema, "internal_reference") != "#/$defs/internal_reference":
        failures.append(f"{schema_path.name}.internal_reference must be internal-only")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + [f"{schema_path.name} missing $defs object"]

    state_def = defs.get("source_dependency_state")
    if not isinstance(state_def, dict) or state_def.get("enum") != (
        ALLOWED_SOURCE_DEPENDENCY_STATES
    ):
        failures.append(
            f"{schema_path.name} source_dependency_state must allow only "
            + ", ".join(ALLOWED_SOURCE_DEPENDENCY_STATES)
        )

    placeholder_def = defs.get("source_required_placeholder")
    if not isinstance(placeholder_def, dict):
        failures.append(f"{schema_path.name} missing source_required_placeholder definition")
    else:
        failures.extend(
            _validate_placeholder_definition(
                placeholder_def,
                schema_name=schema_path.name,
            )
        )
    return failures


def _validate_schema_surfaces(schema_dir: pathlib.Path) -> list[str]:
    failures = _validate_schema_file_set(schema_dir)
    for surface_name in EXPECTED_ADAPTER_SURFACES:
        schema_path = schema_dir / EXPECTED_SCHEMA_FILES[surface_name]
        schema, schema_failures = _load_json(schema_path)
        failures.extend(schema_failures)
        if schema is not None:
            failures.extend(
                _validate_schema_contract(
                    schema,
                    surface_name=surface_name,
                    schema_path=schema_path,
                )
            )
            failures.extend(_validate_no_forbidden_string_values(schema, label=schema_path.name))
    return failures


def _validate_schema_contracts(
    contracts: Any,
    *,
    schema_dir: pathlib.Path,
) -> list[str]:
    if not isinstance(contracts, list):
        return ["adapter_schema_contracts must be a list"]
    failures: list[str] = []
    if len(contracts) != len(EXPECTED_ADAPTER_SURFACES):
        failures.append(
            "adapter_schema_contracts must contain exactly one contract per adapter surface"
        )

    seen_surfaces: list[str] = []
    for index, contract in enumerate(contracts):
        label = f"adapter_schema_contracts[{index}]"
        if not isinstance(contract, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(contract, CONTRACT_FIELDS, label))
        surface_name = contract.get("surface_name")
        if isinstance(surface_name, str):
            seen_surfaces.append(surface_name)
        if surface_name not in EXPECTED_SCHEMA_FILES:
            failures.append(f"{label}.surface_name must be an expected adapter surface")
            continue
        expected_path = pathlib.PurePosixPath(
            "schemas/venue_neutral_prediction_adapter"
        ) / EXPECTED_SCHEMA_FILES[surface_name]
        if contract.get("schema_path") != str(expected_path):
            failures.append(f"{label}.schema_path must be {expected_path}")
        if not (schema_dir / EXPECTED_SCHEMA_FILES[surface_name]).exists():
            failures.append(f"{label}.schema_path target must exist")
        if contract.get("source_dependency_state_allowed_values") != (
            ALLOWED_SOURCE_DEPENDENCY_STATES
        ):
            failures.append(
                f"{label}.source_dependency_state_allowed_values must match allowed states"
            )
        for field, expected_value in sorted(CONTRACT_FLAG_EXPECTATIONS.items()):
            if contract.get(field) != expected_value:
                failures.append(f"{label}.{field} must be {expected_value}")

    if seen_surfaces != EXPECTED_ADAPTER_SURFACES:
        failures.append(
            "adapter_schema_contracts must preserve the expected adapter surface order"
        )
    return failures


def _validate_prerequisite_receipts(receipts: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        receipts,
        PREREQUISITE_RECEIPT_FIELDS,
        "prerequisite_receipts",
    )
    for field, expected_value in sorted(PREREQUISITE_RECEIPT_EXPECTATIONS.items()):
        if receipts.get(field) != expected_value:
            failures.append(f"prerequisite_receipts.{field} must be {expected_value}")
    if receipts.get("backbone_manifest_receipt_status") not in {
        "REQUIRED",
        "REQUIRED_PENDING",
    }:
        failures.append(
            "prerequisite_receipts.backbone_manifest_receipt_status must be "
            "REQUIRED or REQUIRED_PENDING"
        )
    return failures


def _validate_source_dependency_policy(policy: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(
        policy,
        SOURCE_DEPENDENCY_POLICY_FIELDS,
        "source_dependency_policy",
    )
    if policy.get("allowed_source_dependency_states") != ALLOWED_SOURCE_DEPENDENCY_STATES:
        failures.append(
            "source_dependency_policy.allowed_source_dependency_states must match allowed states"
        )
    for field, expected_value in sorted(SOURCE_DEPENDENCY_POLICY_EXPECTATIONS.items()):
        if policy.get(field) != expected_value:
            failures.append(f"source_dependency_policy.{field} must be {expected_value}")
    return failures


def _validate_placeholder_records(records: Any) -> list[str]:
    if not isinstance(records, list) or not records:
        return ["placeholder_records must be a non-empty list"]
    failures: list[str] = []
    for index, record in enumerate(records):
        label = f"placeholder_records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{label} must be an object")
            continue
        expected_fields = PLACEHOLDER_FIELDS | {"placeholder_id"}
        failures.extend(_require_exact_fields(record, expected_fields, label))
        failures.extend(_validate_source_required_placeholder_metadata(record, label))
        if record.get("source_dependency_state") not in ALLOWED_SOURCE_DEPENDENCY_STATES:
            failures.append(f"{label}.source_dependency_state must be allowed")
    return failures


def _validate_source_required_placeholder_metadata(
    value: dict[str, Any],
    label: str,
) -> list[str]:
    if (
        value.get("placeholder_type") != "SOURCE_REQUIRED_PLACEHOLDER"
        and value.get("source_dependency_state") != "SOURCE_REQUIRED_PLACEHOLDER"
    ):
        return []
    failures: list[str] = []
    for field in [
        "target_field_path",
        "dependency_class",
        "blocker_code",
        "acceptance_route",
    ]:
        if not isinstance(value.get(field), str) or not value.get(field):
            failures.append(
                f"{label} SOURCE_REQUIRED_PLACEHOLDER must include {field}"
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
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="venue-neutral adapter validation",
        )
    )
    return failures


def _validate_no_forbidden_string_values(value: dict[str, Any], *, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(value, label):
        if not isinstance(item, str):
            continue
        if key in {"$schema", "$id", "$ref", "pattern"}:
            continue
        lowered = item.lower()
        for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
            if fragment in lowered:
                failures.append(f"{path} contains forbidden adapter fragment: {fragment}")
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_FLAGS
        | {
            field
            for expectations in [
                ADAPTER_GATE_AUTHORITY_EXPECTATIONS,
                PREREQUISITE_RECEIPT_EXPECTATIONS,
                SOURCE_DEPENDENCY_POLICY_EXPECTATIONS,
                CONNECTOR_SCAFFOLD_POLICY_EXPECTATIONS,
                CONNECTOR_SEMANTIC_POLICY_EXPECTATIONS,
                SELECTION_POLICY_EXPECTATIONS,
                RUNTIME_POLICY_EXPECTATIONS,
                EXECUTION_POLICY_EXPECTATIONS,
                LIVE_REACHABILITY_POLICY_EXPECTATIONS,
                ORDER_AUTHORITY_POLICY_EXPECTATIONS,
                SOURCE_AUTHORITY_POLICY_EXPECTATIONS,
                ATOMICROWS_STATE_EXPECTATIONS,
                CLAIM_POLICY_EXPECTATIONS,
            ]
            for field, expected in expectations.items()
            if expected is False
        }
    )
    must_be_true = {
        field
        for expectations in [
            ADAPTER_GATE_AUTHORITY_EXPECTATIONS,
            PREREQUISITE_RECEIPT_EXPECTATIONS,
            SOURCE_DEPENDENCY_POLICY_EXPECTATIONS,
            CONNECTOR_SCAFFOLD_POLICY_EXPECTATIONS,
        ]
        for field, expected in expectations.items()
        if expected is True
    }

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain AtomicRows row records")
        if key == "source_dependency_state" and item not in ALLOWED_SOURCE_DEPENDENCY_STATES:
            failures.append(f"{path} must be an allowed source dependency state")
        if isinstance(item, dict):
            failures.extend(_validate_source_required_placeholder_metadata(item, path))
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime or venue values")
        if key.endswith("_reference") and key not in {
            "accepted_source_packet_reference",
            "runtime_resolver_snapshot_reference",
            "venue_specific_connector_module_reference",
            "implementation_reference",
        }:
            continue
        if key.endswith("_reference") and item != "UNBOUND":
            failures.append(f"{path} must remain UNBOUND")
    return failures


def validate_venue_neutral_prediction_adapter_gate_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
    schema_dir: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "venue-neutral adapter gate fixture",
    )
    for field, expected_value in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected_value:
            failures.append(
                f"venue-neutral adapter gate fixture.{field} must be {expected_value}"
            )

    if fixture.get("expected_adapter_surfaces") != EXPECTED_ADAPTER_SURFACES:
        failures.append("expected_adapter_surfaces must match required adapter surfaces")

    authority, authority_failures = _mapping(
        fixture,
        "adapter_gate_authority",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(authority_failures)
    if authority is not None:
        failures.extend(
            _validate_const_map(
                authority,
                ADAPTER_GATE_AUTHORITY_EXPECTATIONS,
                "adapter_gate_authority",
            )
        )

    failures.extend(
        _validate_schema_contracts(
            fixture.get("adapter_schema_contracts"),
            schema_dir=schema_dir,
        )
    )

    prerequisites, prerequisite_failures = _mapping(
        fixture,
        "prerequisite_receipts",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(prerequisite_failures)
    if prerequisites is not None:
        failures.extend(_validate_prerequisite_receipts(prerequisites))

    source_policy, source_failures = _mapping(
        fixture,
        "source_dependency_policy",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(source_failures)
    if source_policy is not None:
        failures.extend(_validate_source_dependency_policy(source_policy))

    failures.extend(_validate_placeholder_records(fixture.get("placeholder_records")))

    for field, expectations in [
        ("connector_scaffold_policy", CONNECTOR_SCAFFOLD_POLICY_EXPECTATIONS),
        ("connector_semantic_policy", CONNECTOR_SEMANTIC_POLICY_EXPECTATIONS),
        ("selection_policy", SELECTION_POLICY_EXPECTATIONS),
        ("runtime_policy", RUNTIME_POLICY_EXPECTATIONS),
        ("execution_policy", EXECUTION_POLICY_EXPECTATIONS),
        ("live_reachability_policy", LIVE_REACHABILITY_POLICY_EXPECTATIONS),
        ("order_authority_policy", ORDER_AUTHORITY_POLICY_EXPECTATIONS),
        ("source_authority_policy", SOURCE_AUTHORITY_POLICY_EXPECTATIONS),
        ("claim_policy", CLAIM_POLICY_EXPECTATIONS),
    ]:
        policy, policy_failures = _mapping(
            fixture,
            field,
            "venue-neutral adapter gate fixture",
        )
        failures.extend(policy_failures)
        if policy is not None:
            failures.extend(_validate_const_map(policy, expectations, field))

    atomicrows, atomicrows_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(atomicrows_failures)
    if atomicrows is not None:
        failures.extend(_validate_atomicrows_state(atomicrows, repo_root=repo_root))

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(action_failures)
    if forbidden_actions is not None:
        failures.extend(
            _validate_const_map(
                forbidden_actions,
                {field: False for field in FORBIDDEN_ACTION_FLAGS},
                "forbidden_action_flags",
            )
        )

    no_claims, no_claim_failures = _mapping(
        fixture,
        "no_claim_flags",
        "venue-neutral adapter gate fixture",
    )
    failures.extend(no_claim_failures)
    if no_claims is not None:
        failures.extend(
            _validate_const_map(
                no_claims,
                {field: False for field in NO_CLAIM_FLAGS},
                "no_claim_flags",
            )
        )

    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")

    failures.extend(_validate_no_forbidden_claims(fixture))
    failures.extend(_validate_no_forbidden_string_values(fixture, label="fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    schema_dir: pathlib.Path,
    fixture_path: pathlib.Path,
) -> list[str]:
    failures = _validate_schema_surfaces(schema_dir)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(fixture_failures)
    if fixture is not None:
        failures.extend(
            validate_venue_neutral_prediction_adapter_gate_fixture(
                fixture,
                repo_root=repo_root,
                schema_dir=schema_dir,
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--schema-dir", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        repo_root=pathlib.Path(args.repo_root),
        schema_dir=pathlib.Path(args.schema_dir),
        fixture_path=pathlib.Path(args.fixture),
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
