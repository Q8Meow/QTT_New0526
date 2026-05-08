#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "CONNECTOR_CAPABILITY_STATIC_VALIDATION_OK"

CONNECTOR_AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "source_required": True,
    "execution_disabled": True,
    "deterministic_static_fixture_only": True,
    "synthetic_records_only": True,
    "accepted_source_evidence_required_before_semantic_binding": True,
    "accepted_source_evidence_present": False,
    "connector_semantics_unbound": True,
    "connector_semantic_binding_allowed": False,
    "runtime_use_allowed": False,
    "live_use_allowed": False,
    "private_state_fetch_allowed": False,
    "order_execution_allowed": False,
    "profit_claim_allowed": False,
    "source_retrieval_allowed": False,
    "source_acceptance_allowed": False,
    "external_fact_acceptance_allowed": False,
}

CONNECTOR_FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "connector_binding_enabled",
    "semantic_value_population_enabled",
    "runtime_enabled",
    "live_enabled",
    "live_reachability_enabled",
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "position_fetch_enabled",
    "open_orders_fetch_enabled",
    "order_execution_enabled",
    "order_cancel_enabled",
    "order_reduce_close_enabled",
    "profit_claim_enabled",
    "atomicrows_bundle_creation_enabled",
    "sha_freeze_enabled",
}

CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "connector_semantic_value_authority",
    "runtime_authority",
    "live_reachability_authority",
    "runtime_cash_fetch_authority",
    "private_state_fetch_authority",
    "balance_fetch_authority",
    "position_fetch_authority",
    "open_orders_fetch_authority",
    "order_execution_authority",
    "replay_paper_live_execution_authority",
    "network_io_authority",
    "atomicrows_bundle_authority",
    "sha_freeze_authority",
    "profit_claim_authority",
}

ROOT_DISABLED_GUARDRAIL_FIELDS = {
    "connector_semantic_binding_allowed",
    "live_connector_allowed",
    "api_key_required_or_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "order_execution_allowed",
    "runtime_cash_fetch_allowed",
    "profit_claim_allowed",
    "source_retrieval_allowed",
    "external_fact_acceptance_allowed",
    "connector_runtime_allowed",
    "live_reachability_allowed",
    "balance_fetch_allowed",
    "position_fetch_allowed",
    "open_orders_fetch_allowed",
    "atomicrows_bundle_creation_allowed",
    "sha_freeze_allowed",
}

FIXTURE_NO_CLAIM_FIELDS = {
    "contains_real_connector",
    "contains_credentials",
    "contains_real_url",
    "contains_live_endpoint",
    "contains_venue_api_semantics",
    "contains_accepted_source_facts",
    "contains_connector_semantic_values",
    "unlocks_connector_semantics",
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_evidence",
    "fetches_private_state",
    "fetches_balances",
    "fetches_positions",
    "fetches_open_orders",
    "fetches_runtime_cash",
    "executes_orders",
    "cancels_orders",
    "reduces_or_closes_orders",
    "creates_atomicrows_bundle",
    "computes_sha_freeze_authority",
    "creates_profit_evidence",
}

SOURCE_REQUIRED_FIELD_KEYS = {
    "connector_semantic_values",
    "connector_api_surface_fields",
    "credential_fields",
    "live_endpoint",
    "private_state_fields",
    "balance_fields",
    "position_fields",
    "open_order_fields",
    "order_authority_fields",
    "semantic_value",
}

REAL_CONNECTOR_FIELD_KEYS = SOURCE_REQUIRED_FIELD_KEYS | {
    "base_url",
    "endpoint_url",
    "websocket_url",
    "rest_url",
    "account_id",
    "cash_balance",
    "balance",
    "position",
    "positions",
    "open_orders",
    "order_id",
    "submit_order_endpoint",
    "cancel_order_endpoint",
    "reduce_order_endpoint",
    "close_order_endpoint",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
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
    "-----begin",
}

REQUIRED_SURFACE_DEFS = {
    "connector_authority_scope_flags": set(CONNECTOR_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
    "connector_forbidden_action_flags": CONNECTOR_FORBIDDEN_ACTION_FLAGS,
    "no_claim_flags": CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS,
    "connector_source_required_field_placeholders": SOURCE_REQUIRED_FIELD_KEYS
    - {"semantic_value"},
    "connector_capability_card": {
        "card_type",
        "card_id",
        "connector_id",
        "connector_display_name",
        "capability_state",
        "source_evidence_state",
        "semantic_binding_state",
        "runtime_state",
        "accepted_source_evidence_present",
        "connector_semantic_binding_allowed",
        "connector_runtime_enabled",
        "connector_live_enabled",
        "accepted_source_packet_reference",
        "source_required_fields",
        "connector_authority_scope_flags",
        "connector_forbidden_action_flags",
        "no_claim_flags",
    },
    "connector_readiness_record": {
        "record_type",
        "record_id",
        "card_id",
        "capability_family",
        "target_field_path",
        "capability_state",
        "semantic_value",
        "semantic_value_state",
        "semantic_binding_state",
        "execution_state",
        "accepted_source_evidence_present",
        "accepted_source_packet_authority_present",
        "connector_semantic_binding_claim_present",
        "accepted_source_packet_reference",
        "source_required_fields",
        "connector_authority_scope_flags",
        "connector_forbidden_action_flags",
        "no_claim_flags",
    },
    "connector_capability_registry": {
        "registry_type",
        "registry_id",
        "registry_authority_class",
        "mode",
        "execution",
        "deterministic_output",
        "connector_authority_scope_flags",
        "connector_forbidden_action_flags",
        "capability_cards",
        "readiness_records",
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
    "connector_capability_registry",
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


def _mapping_at(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _list_at(value: dict[str, Any], field: str, label: str) -> tuple[list[Any] | None, list[str]]:
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
        set(CONNECTOR_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
        label,
    )
    for field, expected in sorted(CONNECTOR_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
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
        CONNECTOR_FORBIDDEN_ACTION_FLAGS
        | CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS
        | ROOT_DISABLED_GUARDRAIL_FIELDS
        | FIXTURE_NO_CLAIM_FIELDS
        | {
            "accepted_source_evidence_present",
            "accepted_source_packet_authority_present",
            "connector_semantic_binding_claim_present",
            "connector_semantic_binding_allowed",
            "connector_runtime_enabled",
            "connector_live_enabled",
        }
    )
    for path, key, item in _walk_values(value):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
    return failures


def _validate_source_required_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk_values(value):
        if key in REAL_CONNECTOR_FIELD_KEYS and item != "SOURCE_REQUIRED":
            failures.append(f"{path} must remain SOURCE_REQUIRED")
    return failures


def _validate_no_forbidden_text(value: dict[str, Any]) -> list[str]:
    raw_text = json.dumps(value, sort_keys=True).lower()
    return [
        f"fixture contains forbidden connector/live/source fragment: {fragment}"
        for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS)
        if fragment in raw_text
    ]


def _validate_semantic_claims_require_evidence(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk_values(value):
        if key != "connector_semantic_binding_claim_present" or item is not True:
            continue
        owner_path = path.rsplit(".", 1)[0]
        owner = value
        for part in owner_path.removeprefix("fixture.").split("."):
            if not part:
                continue
            if "[" in part:
                field, index_text = part.rstrip("]").split("[")
                owner = owner[field][int(index_text)]
            else:
                owner = owner[part]
        if not isinstance(owner, dict) or owner.get("accepted_source_evidence_present") is not True:
            failures.append(f"{path} requires accepted source evidence before binding")
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
        "connector_capability_registry",
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
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_AUTHORITY"
    ):
        failures.append("schema root authority class must be static non-connector")
    if _const_value(schema, "surface_kind") != (
        "CONNECTOR_CAPABILITY_REGISTRY_STATIC_SCAFFOLD"
    ):
        failures.append("schema root surface kind must be connector capability registry")

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

    for field in sorted(CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS):
        no_claim_def = defs.get("no_claim_flags")
        if isinstance(no_claim_def, dict) and _const_value(no_claim_def, field) is not False:
            failures.append(f"no_claim_flags must set {field} to const false")

    for field in sorted(CONNECTOR_FORBIDDEN_ACTION_FLAGS):
        action_def = defs.get("connector_forbidden_action_flags")
        if isinstance(action_def, dict) and _const_value(action_def, field) is not False:
            failures.append(f"connector forbidden flag {field} must be const false")

    scope_def = defs.get("connector_authority_scope_flags")
    if isinstance(scope_def, dict):
        for field, expected in sorted(CONNECTOR_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
            if _const_value(scope_def, field) is not expected:
                failures.append(
                    f"connector authority/scope flag {field} must be const {expected}"
                )

    source_required_def = defs.get("connector_source_required_field_placeholders")
    if isinstance(source_required_def, dict):
        for field in sorted(SOURCE_REQUIRED_FIELD_KEYS - {"semantic_value"}):
            if field in _properties(source_required_def) and (
                _properties(source_required_def)[field].get("$ref")
                != "#/$defs/source_required_value"
            ):
                failures.append(f"{field} must reference source_required_value")

    return failures


def validate_connector_capability_registry_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _require_mapping_fields(
            fixture,
            FIXTURE_REQUIRED_ROOT_FIELDS,
            "connector capability fixture",
        )
    )

    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_CONNECTOR_NOT_SOURCE_FACT"
    ):
        failures.append("connector capability fixture must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
    ):
        failures.append("connector capability fixture example authority must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("connector capability fixture mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("connector capability fixture execution must be DISABLED")
    if fixture.get("schema_authority_class") != (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_AUTHORITY"
    ):
        failures.append("connector capability fixture schema authority must be static-only")
    if fixture.get("surface_kind") != "CONNECTOR_CAPABILITY_REGISTRY_STATIC_SCAFFOLD":
        failures.append("connector capability fixture surface kind must be registry scaffold")
    if fixture.get("deterministic_output") is not True:
        failures.append("connector capability fixture deterministic_output must be true")

    fixture_no_claim_flags, fixture_flag_failures = _mapping_at(
        fixture, "fixture_no_claim_flags", "connector capability fixture"
    )
    failures.extend(fixture_flag_failures)
    if fixture_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                fixture_no_claim_flags,
                FIXTURE_NO_CLAIM_FIELDS,
                "connector capability fixture.fixture_no_claim_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(
        fixture, "no_claim_flags", "connector capability fixture"
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS,
                "connector capability fixture.no_claim_flags",
            )
        )

    registry, registry_failures = _mapping_at(
        fixture,
        "connector_capability_registry",
        "connector capability fixture",
    )
    failures.extend(registry_failures)
    if registry is None:
        return failures

    failures.extend(
        _require_mapping_fields(
            registry,
            REQUIRED_SURFACE_DEFS["connector_capability_registry"],
            "connector_capability_registry",
        )
    )
    if registry.get("registry_type") != "CONNECTOR_CAPABILITY_REGISTRY_STATIC_SCAFFOLD":
        failures.append("connector_capability_registry.registry_type must be static scaffold")
    if registry.get("registry_authority_class") != (
        "STATIC_CONNECTOR_CAPABILITY_REGISTRY_SCAFFOLD_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append("connector_capability_registry authority class must be static-only")
    if registry.get("mode") != "SOURCE_REQUIRED":
        failures.append("connector_capability_registry mode must be SOURCE_REQUIRED")
    if registry.get("execution") != "DISABLED":
        failures.append("connector_capability_registry execution must be DISABLED")
    if registry.get("deterministic_output") is not True:
        failures.append("connector_capability_registry deterministic_output must be true")

    scope_flags, scope_failures = _mapping_at(
        registry,
        "connector_authority_scope_flags",
        "connector_capability_registry",
    )
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_authority_scope_flag_map(
                scope_flags,
                "connector_capability_registry.connector_authority_scope_flags",
            )
        )

    action_flags, action_failures = _mapping_at(
        registry,
        "connector_forbidden_action_flags",
        "connector_capability_registry",
    )
    failures.extend(action_failures)
    if action_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                action_flags,
                CONNECTOR_FORBIDDEN_ACTION_FLAGS,
                "connector_capability_registry.connector_forbidden_action_flags",
            )
        )

    registry_no_claim_flags, registry_no_claim_failures = _mapping_at(
        registry,
        "no_claim_flags",
        "connector_capability_registry",
    )
    failures.extend(registry_no_claim_failures)
    if registry_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                registry_no_claim_flags,
                CONNECTOR_NO_CLAIM_AUTHORITY_FIELDS,
                "connector_capability_registry.no_claim_flags",
            )
        )

    card_records, card_failures = _list_at(
        registry, "capability_cards", "connector_capability_registry"
    )
    failures.extend(card_failures)
    if card_records is not None:
        for index, card in enumerate(card_records):
            label = f"connector_capability_registry.capability_cards[{index}]"
            if not isinstance(card, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_mapping_fields(
                    card,
                    REQUIRED_SURFACE_DEFS["connector_capability_card"],
                    label,
                )
            )
            if card.get("capability_state") != "SOURCE_REQUIRED":
                failures.append(f"{label}.capability_state must be SOURCE_REQUIRED")
            if card.get("semantic_binding_state") != "UNBOUND":
                failures.append(f"{label}.semantic_binding_state must be UNBOUND")
            if card.get("runtime_state") != "DISABLED":
                failures.append(f"{label}.runtime_state must be DISABLED")

    readiness_records, readiness_failures = _list_at(
        registry, "readiness_records", "connector_capability_registry"
    )
    failures.extend(readiness_failures)
    if readiness_records is not None:
        for index, record in enumerate(readiness_records):
            label = f"connector_capability_registry.readiness_records[{index}]"
            if not isinstance(record, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_mapping_fields(
                    record,
                    REQUIRED_SURFACE_DEFS["connector_readiness_record"],
                    label,
                )
            )
            if record.get("capability_state") != "SOURCE_REQUIRED":
                failures.append(f"{label}.capability_state must be SOURCE_REQUIRED")
            if record.get("semantic_value") != "SOURCE_REQUIRED":
                failures.append(f"{label}.semantic_value must be SOURCE_REQUIRED")
            if record.get("semantic_value_state") != "SOURCE_REQUIRED":
                failures.append(f"{label}.semantic_value_state must be SOURCE_REQUIRED")
            if record.get("semantic_binding_state") != "UNBOUND":
                failures.append(f"{label}.semantic_binding_state must be UNBOUND")
            if record.get("execution_state") != "DISABLED":
                failures.append(f"{label}.execution_state must be DISABLED")

    failures.extend(_validate_no_forbidden_true_values(fixture))
    failures.extend(_validate_source_required_values(fixture))
    failures.extend(_validate_no_forbidden_text(fixture))
    failures.extend(_validate_semantic_claims_require_evidence(fixture))
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
        failures.extend(validate_connector_capability_registry_fixture(fixture))

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
            "CONNECTOR_CAPABILITY_STATIC_VALIDATION_FAILED\n- "
            + "\n- ".join(failures)
        )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
