#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "VENUE_ABSTRACTION_LAYER_STATIC_VALIDATION_OK"

VENUE_AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "source_required": True,
    "execution_disabled": True,
    "scaffold_only": True,
    "deterministic_static_fixture_only": True,
    "synthetic_records_only": True,
    "venue_neutral_interfaces_only": True,
    "accepted_source_evidence_required_before_semantic_binding": True,
    "accepted_source_evidence_present": False,
    "connector_semantics_unbound": True,
    "venue_semantics_source_required": True,
    "venue_specific_semantic_values_allowed": False,
    "external_fact_acceptance_allowed": False,
    "source_retrieval_allowed": False,
    "source_acceptance_allowed": False,
    "connector_binding_allowed": False,
    "connector_semantic_binding_allowed": False,
    "runtime_use_allowed": False,
    "runtime_execution_allowed": False,
    "runtime_trading_allowed": False,
    "runtime_resolver_snapshot_creation_allowed": False,
    "replay_execution_allowed": False,
    "paper_execution_allowed": False,
    "replay_result_packet_creation_allowed": False,
    "paper_result_packet_creation_allowed": False,
    "live_use_allowed": False,
    "live_reachability_allowed": False,
    "live_endpoint_allowed": False,
    "live_client_allowed": False,
    "private_state_fetch_allowed": False,
    "private_state_materialization_allowed": False,
    "runtime_cash_fetch_allowed": False,
    "runtime_cash_receipt_creation_allowed": False,
    "order_execution_allowed": False,
    "order_authority_allowed": False,
    "network_io_allowed": False,
    "atomicrows_bundle_creation_allowed": False,
    "sha_freeze_authority_allowed": False,
    "blocker_reduction_allowed": False,
    "profit_claim_allowed": False,
}

VENUE_FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "accepted_source_packet_creation_enabled",
    "connector_binding_enabled",
    "semantic_value_population_enabled",
    "venue_specific_semantic_population_enabled",
    "runtime_enabled",
    "runtime_execution_enabled",
    "runtime_trading_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "runtime_resolver_snapshot_materialization_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "replay_paper_execution_enabled",
    "replay_result_packet_creation_enabled",
    "paper_result_packet_creation_enabled",
    "live_enabled",
    "live_reachability_enabled",
    "live_endpoint_enabled",
    "live_client_enabled",
    "private_state_fetch_enabled",
    "private_state_materialization_enabled",
    "balance_fetch_enabled",
    "position_fetch_enabled",
    "open_orders_fetch_enabled",
    "runtime_cash_fetch_enabled",
    "runtime_cash_receipt_creation_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_close_enabled",
    "network_io_enabled",
    "atomicrows_bundle_creation_enabled",
    "sha_freeze_enabled",
    "blocker_reduction_enabled",
    "profit_claim_enabled",
}

NO_CLAIM_AUTHORITY_FIELDS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "connector_semantic_value_authority",
    "venue_abstraction_runtime_authority",
    "venue_semantic_value_authority",
    "runtime_authority",
    "runtime_execution_authority",
    "runtime_trading_authority",
    "runtime_resolver_snapshot_authority",
    "replay_execution_authority",
    "paper_execution_authority",
    "replay_result_packet_authority",
    "paper_result_packet_authority",
    "live_reachability_authority",
    "runtime_cash_fetch_authority",
    "runtime_cash_receipt_authority",
    "private_state_fetch_authority",
    "balance_fetch_authority",
    "position_fetch_authority",
    "open_orders_fetch_authority",
    "order_execution_authority",
    "order_cancel_authority",
    "order_reduce_close_authority",
    "network_io_authority",
    "atomicrows_bundle_authority",
    "sha_freeze_authority",
    "blocker_reduction_authority",
    "profit_claim_authority",
}

FIXTURE_NO_CLAIM_FIELDS = {
    "contains_real_contract_identifier",
    "contains_real_event_identifier",
    "contains_real_venue_identifier",
    "contains_real_market_identifier",
    "contains_real_connector_identifier",
    "contains_real_url",
    "contains_credentials",
    "contains_accepted_source_facts",
    "contains_connector_semantic_values",
    "contains_venue_specific_semantic_values",
    "contains_market_data_schema",
    "contains_order_semantics",
    "contains_private_state",
    "contains_balance_value",
    "contains_position_value",
    "contains_open_orders",
    "contains_runtime_resolver_snapshot",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_runtime_cash_receipt",
    "contains_order_instruction",
    "contains_order_receipt",
    "contains_atomicrows_bundle",
    "contains_sha_freeze_authority",
    "retrieves_source_facts",
    "accepts_source_facts",
    "accepts_external_facts",
    "binds_connector",
    "binds_connector_semantics",
    "fetches_private_state",
    "fetches_balances",
    "fetches_positions",
    "fetches_open_orders",
    "fetches_runtime_cash",
    "creates_runtime_resolver_snapshot",
    "executes_replay",
    "executes_paper",
    "creates_replay_result",
    "creates_paper_result",
    "creates_runtime_cash_receipts",
    "executes_orders",
    "cancels_orders",
    "reduces_or_closes_orders",
    "creates_atomicrows_bundle",
    "computes_sha_freeze_authority",
    "reduces_blockers",
    "creates_profit_evidence",
}

ROOT_DISABLED_GUARDRAIL_FIELDS = {
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "external_fact_acceptance_allowed",
    "connector_binding_allowed",
    "connector_semantic_binding_allowed",
    "runtime_execution_allowed",
    "runtime_trading_allowed",
    "runtime_resolver_snapshot_creation_allowed",
    "replay_execution_allowed",
    "paper_execution_allowed",
    "live_reachability_allowed",
    "live_endpoint_allowed",
    "live_client_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "order_execution_allowed",
    "atomicrows_bundle_creation_allowed",
    "sha_freeze_authority_allowed",
    "blocker_reduction_allowed",
    "profit_claim_allowed",
}

FALSE_SURFACE_FIELDS = {
    "accepted_source_evidence_present",
    "connector_binding_allowed",
    "connector_semantic_binding_allowed",
    "contains_accepted_source_fact",
    "contains_balance_value",
    "contains_connector_semantic_values",
    "contains_open_orders",
    "contains_order_instruction",
    "contains_order_receipt",
    "contains_paper_result_packet",
    "contains_position_value",
    "contains_real_market_identifier",
    "contains_replay_result_packet",
    "contains_runtime_cash_receipt",
    "contains_runtime_resolver_snapshot",
    "live_client_present",
    "live_endpoint_present",
    "market_data_runtime_allowed",
    "order_authority_present",
    "order_execution_allowed",
    "order_intent_runtime_allowed",
    "private_state_fetch_allowed",
    "private_state_present",
}

SOURCE_REQUIRED_SEMANTIC_FIELD_KEYS = {
    "balance_semantics",
    "capability_reference_semantics",
    "connector_capability_semantics",
    "fee_semantics",
    "market_data_normalization_rules",
    "market_data_schema",
    "market_data_snapshot_semantics",
    "market_data_stream_semantics",
    "open_orders_semantics",
    "order_intent_semantics",
    "order_lifecycle_semantics",
    "order_price_semantics",
    "order_quantity_semantics",
    "order_side_semantics",
    "order_time_in_force_semantics",
    "order_type_semantics",
    "payout_semantics",
    "position_semantics",
    "private_state_semantics",
    "rate_limit_semantics",
    "settlement_semantics",
    "tick_semantics",
}

UNBOUND_REFERENCE_FIELD_KEYS = {
    "account_reference",
    "balance_reference",
    "cash_reference",
    "connector_binding_reference",
    "connector_capability_reference",
    "connector_semantic_value_reference",
    "contract_reference",
    "event_reference",
    "market_data_client_reference",
    "market_data_endpoint_reference",
    "market_reference",
    "open_orders_reference",
    "order_authority_reference",
    "order_client_reference",
    "order_execution_reference",
    "position_reference",
    "private_state_client_reference",
    "private_state_reference",
    "runtime_resolver_snapshot_reference",
    "venue_reference",
}

REQUIRED_SURFACE_DEFS = {
    "venue_authority_scope_flags": set(VENUE_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
    "venue_forbidden_action_flags": VENUE_FORBIDDEN_ACTION_FLAGS,
    "no_claim_flags": NO_CLAIM_AUTHORITY_FIELDS,
    "source_required_venue_semantic_fields": SOURCE_REQUIRED_SEMANTIC_FIELD_KEYS,
    "market_data_surface_contract": {
        "surface_type",
        "surface_id",
        "surface_state",
        "semantic_binding_state",
        "runtime_state",
        "source_required_semantic_fields",
        "venue_reference",
        "market_reference",
        "contract_reference",
        "event_reference",
        "market_data_endpoint_reference",
        "market_data_client_reference",
        "live_endpoint_present",
        "live_client_present",
        "market_data_runtime_allowed",
        "contains_real_market_identifier",
        "contains_accepted_source_fact",
    },
    "order_intent_surface_contract": {
        "surface_type",
        "surface_id",
        "surface_state",
        "semantic_binding_state",
        "runtime_state",
        "source_required_semantic_fields",
        "order_client_reference",
        "order_authority_reference",
        "order_execution_reference",
        "order_intent_runtime_allowed",
        "order_execution_allowed",
        "order_authority_present",
        "contains_order_instruction",
        "contains_order_receipt",
    },
    "private_state_placeholder_contract": {
        "surface_type",
        "surface_id",
        "surface_state",
        "semantic_binding_state",
        "runtime_state",
        "source_required_semantic_fields",
        "private_state_client_reference",
        "private_state_reference",
        "account_reference",
        "cash_reference",
        "balance_reference",
        "position_reference",
        "open_orders_reference",
        "private_state_fetch_allowed",
        "private_state_present",
        "contains_balance_value",
        "contains_position_value",
        "contains_open_orders",
    },
    "connector_capability_reference_contract": {
        "surface_type",
        "surface_id",
        "surface_state",
        "semantic_binding_state",
        "runtime_state",
        "source_required_semantic_fields",
        "connector_capability_reference",
        "connector_binding_reference",
        "connector_semantic_value_reference",
        "connector_binding_allowed",
        "connector_semantic_binding_allowed",
        "contains_connector_semantic_values",
        "accepted_source_evidence_present",
    },
    "venue_abstraction_layer": {
        "layer_type",
        "layer_id",
        "layer_authority_class",
        "mode",
        "execution",
        "scaffold_state",
        "layer_state",
        "deterministic_output",
        "runtime_resolver_snapshot_reference",
        "contains_runtime_resolver_snapshot",
        "contains_replay_result_packet",
        "contains_paper_result_packet",
        "contains_runtime_cash_receipt",
        "venue_authority_scope_flags",
        "venue_forbidden_action_flags",
        "market_data_surfaces",
        "order_intent_surfaces",
        "private_state_placeholders",
        "connector_capability_references",
        "validation_hook_ids",
        "no_claim_flags",
    },
}

FIXTURE_REQUIRED_ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "example_authority_class",
    "mode",
    "execution",
    "schema_authority_class",
    "surface_kind",
    "surface_version",
    "deterministic_output",
    "fixture_no_claim_flags",
    "no_claim_flags",
    "venue_abstraction_layer",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "http",
    "kalshi",
    "polymarket",
    "forecast_ex",
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
    "atomicrows.bundle",
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
    if isinstance(prop, dict):
        return prop.get("const")
    return None


def _mapping_at(
    value: dict[str, Any], field: str, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _list_at(
    value: dict[str, Any], field: str, label: str
) -> tuple[list[Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, list) or not item:
        return None, [f"{label}.{field} must be a non-empty list"]
    return item, []


def _require_mapping_fields(
    value: dict[str, Any], required_fields: set[str], label: str
) -> list[str]:
    missing = sorted(required_fields - set(value))
    if missing:
        return [f"{label} missing required fields: {', '.join(missing)}"]
    return []


def _validate_false_flag_map(
    value: dict[str, Any], required_fields: set[str], label: str
) -> list[str]:
    failures = _require_mapping_fields(value, required_fields, label)
    for field in sorted(required_fields):
        if field in value and value[field] is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def _validate_authority_scope_flag_map(value: dict[str, Any], label: str) -> list[str]:
    failures = _require_mapping_fields(
        value,
        set(VENUE_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
        label,
    )
    for field, expected in sorted(VENUE_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
        if field in value and value[field] is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def _walk_values(value: Any, path: str = "fixture"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk_values(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_values(item, f"{path}[{index}]")


def _validate_no_forbidden_true_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        VENUE_FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_AUTHORITY_FIELDS
        | ROOT_DISABLED_GUARDRAIL_FIELDS
        | FALSE_SURFACE_FIELDS
        | FIXTURE_NO_CLAIM_FIELDS
    )
    for path, key, item in _walk_values(value):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
    return failures


def _validate_source_required_semantic_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk_values(value):
        if key in SOURCE_REQUIRED_SEMANTIC_FIELD_KEYS and item != "SOURCE_REQUIRED":
            failures.append(f"{path} must remain SOURCE_REQUIRED")
    return failures


def _validate_unbound_reference_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk_values(value):
        if key in UNBOUND_REFERENCE_FIELD_KEYS and item != "UNBOUND":
            failures.append(f"{path} must remain UNBOUND")
    return failures


def _validate_no_forbidden_text(value: dict[str, Any]) -> list[str]:
    raw_text = json.dumps(value, sort_keys=True).lower()
    return [
        f"fixture contains forbidden venue/live/source fragment: {fragment}"
        for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS)
        if fragment in raw_text
    ]


def _validate_no_numeric_runtime_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, _key, item in _walk_values(value):
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime or venue values")
    return failures


def _validate_schema_surfaces(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    properties = _properties(schema)
    required = _required(schema)
    root_required = {
        "mode",
        "execution",
        "schema_authority_class",
        "surface_kind",
        "surface_version",
        "deterministic_output",
        "no_claim_flags",
        "venue_abstraction_layer",
    }
    failures.extend(_require_mapping_fields(properties, root_required, "schema.properties"))
    missing_required = sorted(root_required - required)
    if missing_required:
        failures.append(f"schema root missing required fields: {', '.join(missing_required)}")

    if _const_value(schema, "mode") != "SOURCE_REQUIRED":
        failures.append("schema root mode must be SOURCE_REQUIRED")
    if _const_value(schema, "execution") != "DISABLED":
        failures.append("schema root execution must be DISABLED")
    if _const_value(schema, "schema_authority_class") != (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_VENUE_AUTHORITY"
    ):
        failures.append("schema root authority class must be static non-venue")
    if _const_value(schema, "surface_kind") != (
        "VENUE_ABSTRACTION_LAYER_STATIC_SCAFFOLD"
    ):
        failures.append("schema root surface kind must be venue abstraction scaffold")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema missing $defs object"]

    for surface_name, required_fields in sorted(REQUIRED_SURFACE_DEFS.items()):
        surface = defs.get(surface_name)
        if not isinstance(surface, dict):
            failures.append(f"schema missing required surface definition: {surface_name}")
            continue
        surface_properties = set(_properties(surface))
        surface_required = _required(surface)
        missing_properties = sorted(required_fields - surface_properties)
        missing_required = sorted(required_fields - surface_required)
        if missing_properties:
            failures.append(
                f"{surface_name} missing properties: {', '.join(missing_properties)}"
            )
        if missing_required:
            failures.append(
                f"{surface_name} missing required fields: {', '.join(missing_required)}"
            )

    no_claim_def = defs.get("no_claim_flags")
    if isinstance(no_claim_def, dict):
        for field in sorted(NO_CLAIM_AUTHORITY_FIELDS):
            if _const_value(no_claim_def, field) is not False:
                failures.append(f"no_claim_flags must set {field} to const false")

    action_def = defs.get("venue_forbidden_action_flags")
    if isinstance(action_def, dict):
        for field in sorted(VENUE_FORBIDDEN_ACTION_FLAGS):
            if _const_value(action_def, field) is not False:
                failures.append(f"venue forbidden flag {field} must be const false")

    scope_def = defs.get("venue_authority_scope_flags")
    if isinstance(scope_def, dict):
        for field, expected in sorted(VENUE_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
            if _const_value(scope_def, field) is not expected:
                failures.append(f"venue authority/scope flag {field} must be const {expected}")

    semantic_def = defs.get("source_required_venue_semantic_fields")
    if isinstance(semantic_def, dict):
        for field in sorted(SOURCE_REQUIRED_SEMANTIC_FIELD_KEYS):
            prop = _properties(semantic_def).get(field, {})
            if not isinstance(prop, dict) or prop.get("$ref") != "#/$defs/source_required_value":
                failures.append(f"{field} must reference source_required_value")

    return failures


def _validate_scope_and_action_maps(owner: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    scope_flags, scope_failures = _mapping_at(owner, "venue_authority_scope_flags", label)
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_authority_scope_flag_map(
                scope_flags, f"{label}.venue_authority_scope_flags"
            )
        )

    action_flags, action_failures = _mapping_at(owner, "venue_forbidden_action_flags", label)
    failures.extend(action_failures)
    if action_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                action_flags,
                VENUE_FORBIDDEN_ACTION_FLAGS,
                f"{label}.venue_forbidden_action_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(owner, "no_claim_flags", label)
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                NO_CLAIM_AUTHORITY_FIELDS,
                f"{label}.no_claim_flags",
            )
        )
    return failures


def _validate_surface_state(surface: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if surface.get("surface_state") != "SOURCE_REQUIRED":
        failures.append(f"{label}.surface_state must be SOURCE_REQUIRED")
    if surface.get("semantic_binding_state") != "UNBOUND":
        failures.append(f"{label}.semantic_binding_state must be UNBOUND")
    if surface.get("runtime_state") != "DISABLED":
        failures.append(f"{label}.runtime_state must be DISABLED")
    semantic_fields, semantic_failures = _mapping_at(
        surface, "source_required_semantic_fields", label
    )
    failures.extend(semantic_failures)
    if semantic_fields is not None:
        failures.extend(
            _require_mapping_fields(
                semantic_fields,
                SOURCE_REQUIRED_SEMANTIC_FIELD_KEYS,
                f"{label}.source_required_semantic_fields",
            )
        )
    return failures


def _validate_surface_list(
    layer: dict[str, Any],
    field: str,
    required_def_name: str,
    expected_surface_type: str,
    label: str,
) -> list[str]:
    failures: list[str] = []
    surfaces, surface_failures = _list_at(layer, field, label)
    failures.extend(surface_failures)
    if surfaces is None:
        return failures
    for index, surface in enumerate(surfaces):
        surface_label = f"{label}.{field}[{index}]"
        if not isinstance(surface, dict):
            failures.append(f"{surface_label} must be an object")
            continue
        failures.extend(
            _require_mapping_fields(
                surface,
                REQUIRED_SURFACE_DEFS[required_def_name],
                surface_label,
            )
        )
        if surface.get("surface_type") != expected_surface_type:
            failures.append(f"{surface_label}.surface_type must be {expected_surface_type}")
        failures.extend(_validate_surface_state(surface, surface_label))
    return failures


def validate_venue_abstraction_layer_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _require_mapping_fields(
            fixture,
            FIXTURE_REQUIRED_ROOT_FIELDS,
            "venue abstraction fixture",
        )
    )

    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_VENUE_AUTHORITY_NOT_SOURCE_FACT"
    ):
        failures.append("venue abstraction fixture must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
    ):
        failures.append("venue abstraction fixture example authority must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("venue abstraction fixture mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("venue abstraction fixture execution must be DISABLED")
    if fixture.get("schema_authority_class") != (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_VENUE_AUTHORITY"
    ):
        failures.append("venue abstraction fixture schema authority must be static-only")
    if fixture.get("surface_kind") != "VENUE_ABSTRACTION_LAYER_STATIC_SCAFFOLD":
        failures.append("venue abstraction fixture surface kind must be venue scaffold")
    if fixture.get("deterministic_output") is not True:
        failures.append("venue abstraction fixture deterministic_output must be true")

    fixture_no_claim_flags, fixture_flag_failures = _mapping_at(
        fixture, "fixture_no_claim_flags", "venue abstraction fixture"
    )
    failures.extend(fixture_flag_failures)
    if fixture_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                fixture_no_claim_flags,
                FIXTURE_NO_CLAIM_FIELDS,
                "venue abstraction fixture.fixture_no_claim_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(
        fixture, "no_claim_flags", "venue abstraction fixture"
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                NO_CLAIM_AUTHORITY_FIELDS,
                "venue abstraction fixture.no_claim_flags",
            )
        )

    layer, layer_failures = _mapping_at(
        fixture,
        "venue_abstraction_layer",
        "venue abstraction fixture",
    )
    failures.extend(layer_failures)
    if layer is None:
        failures.extend(_validate_no_forbidden_true_values(fixture))
        failures.extend(_validate_no_forbidden_text(fixture))
        return failures

    layer_label = "venue_abstraction_layer"
    failures.extend(
        _require_mapping_fields(
            layer,
            REQUIRED_SURFACE_DEFS["venue_abstraction_layer"],
            layer_label,
        )
    )
    if layer.get("layer_type") != "VENUE_ABSTRACTION_LAYER_STATIC_SCAFFOLD":
        failures.append("venue_abstraction_layer.layer_type must be static scaffold")
    if layer.get("layer_authority_class") != (
        "STATIC_VENUE_ABSTRACTION_LAYER_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append("venue_abstraction_layer authority class must be static-only")
    if layer.get("mode") != "SOURCE_REQUIRED":
        failures.append("venue_abstraction_layer mode must be SOURCE_REQUIRED")
    if layer.get("execution") != "DISABLED":
        failures.append("venue_abstraction_layer execution must be DISABLED")
    if layer.get("scaffold_state") != "SCAFFOLD_ONLY":
        failures.append("venue_abstraction_layer scaffold_state must be SCAFFOLD_ONLY")
    if layer.get("layer_state") != "SCAFFOLD_ONLY_NOT_EXECUTABLE":
        failures.append("venue_abstraction_layer layer_state must remain not executable")
    if layer.get("deterministic_output") is not True:
        failures.append("venue_abstraction_layer deterministic_output must be true")
    failures.extend(_validate_scope_and_action_maps(layer, layer_label))
    failures.extend(
        _validate_surface_list(
            layer,
            "market_data_surfaces",
            "market_data_surface_contract",
            "VENUE_NEUTRAL_MARKET_DATA_SURFACE_CONTRACT_PLACEHOLDER",
            layer_label,
        )
    )
    failures.extend(
        _validate_surface_list(
            layer,
            "order_intent_surfaces",
            "order_intent_surface_contract",
            "VENUE_NEUTRAL_ORDER_INTENT_SURFACE_CONTRACT_PLACEHOLDER",
            layer_label,
        )
    )
    failures.extend(
        _validate_surface_list(
            layer,
            "private_state_placeholders",
            "private_state_placeholder_contract",
            "VENUE_NEUTRAL_PRIVATE_STATE_PLACEHOLDER_CONTRACT",
            layer_label,
        )
    )
    failures.extend(
        _validate_surface_list(
            layer,
            "connector_capability_references",
            "connector_capability_reference_contract",
            "CONNECTOR_CAPABILITY_REFERENCE_CONTRACT_PLACEHOLDER",
            layer_label,
        )
    )

    failures.extend(_validate_no_forbidden_true_values(fixture))
    failures.extend(_validate_source_required_semantic_values(fixture))
    failures.extend(_validate_unbound_reference_values(fixture))
    failures.extend(_validate_no_forbidden_text(fixture))
    failures.extend(_validate_no_numeric_runtime_values(fixture))
    return failures


def validate_static_surface(
    *, schema_path: pathlib.Path, fixture_path: pathlib.Path
) -> list[str]:
    failures: list[str] = []
    schema, schema_failures = _load_json(schema_path)
    failures.extend(schema_failures)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(fixture_failures)

    if schema is not None:
        failures.extend(_validate_schema_surfaces(schema))
    if fixture is not None:
        failures.extend(validate_venue_abstraction_layer_fixture(fixture))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
    )
    if failures:
        raise SystemExit(
            "VENUE_ABSTRACTION_LAYER_STATIC_VALIDATION_FAILED\n- "
            + "\n- ".join(failures)
        )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
