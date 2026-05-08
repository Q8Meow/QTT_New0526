#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "ORDER_INTENT_EXECUTION_ROUTER_STATIC_VALIDATION_OK"

TRUE_SCOPE_FLAGS = {
    "source_required",
    "execution_disabled",
    "scaffold_only",
    "deterministic_static_fixture_only",
    "synthetic_records_only",
    "order_intent_placeholder_only",
    "execution_router_gate_placeholder_only",
    "final_order_submission_authority_disabled",
    "accepted_source_evidence_required_before_semantic_binding",
}

FALSE_SCOPE_FLAGS = {
    "accepted_source_evidence_present",
    "source_retrieval_allowed",
    "source_acceptance_allowed",
    "connector_binding_allowed",
    "connector_semantic_binding_allowed",
    "runtime_use_allowed",
    "runtime_execution_allowed",
    "live_use_allowed",
    "private_state_fetch_allowed",
    "order_execution_allowed",
    "profit_claim_allowed",
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "runtime_enabled",
    "runtime_execution_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "replay_result_packet_creation_enabled",
    "paper_result_packet_creation_enabled",
    "live_enabled",
    "live_signer_path_enabled",
    "venue_write_connectivity_enabled",
    "private_state_fetch_enabled",
    "runtime_cash_receipt_creation_enabled",
    "order_execution_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "order_replace_enabled",
    "order_amend_enabled",
    "final_order_release_enabled",
    "atomicrows_bundle_creation_enabled",
    "sha_freeze_enabled",
    "blocker_reduction_enabled",
    "profit_claim_enabled",
}

NO_CLAIM_FLAGS = {
    "contains_real_venue_identifier",
    "contains_real_market_identifier",
    "contains_real_contract_identifier",
    "contains_real_event_identifier",
    "contains_credentials",
    "contains_private_state",
    "contains_accepted_source_facts",
    "contains_connector_semantic_values",
    "contains_venue_specific_order_semantics",
    "contains_order_instruction",
    "contains_order_receipt",
    "contains_order_submission_payload",
    "retrieves_source_facts",
    "accepts_source_facts",
    "binds_connector",
    "binds_connector_semantics",
    "fetches_private_state",
    "creates_runtime_resolver_snapshot",
    "executes_replay",
    "executes_paper",
    "creates_replay_result",
    "creates_paper_result",
    "creates_runtime_cash_receipts",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "replaces_orders",
    "amends_orders",
    "creates_final_order_release_authority",
    "creates_live_signer_path",
    "creates_venue_write_connectivity",
    "creates_atomicrows_bundle",
    "computes_sha_freeze_authority",
    "reduces_blockers",
    "creates_profit_evidence",
}

SEMANTIC_FIELDS = {
    "order_intent_semantics",
    "order_type_semantics",
    "order_side_semantics",
    "order_quantity_semantics",
    "order_price_semantics",
    "order_time_in_force_semantics",
    "order_lifecycle_semantics",
    "router_gate_semantics",
    "final_order_release_semantics",
    "live_signer_path_semantics",
    "venue_write_connectivity_semantics",
}

UNBOUND_REFERENCE_FIELDS = {
    "venue_reference",
    "market_reference",
    "contract_reference",
    "event_reference",
    "connector_reference",
    "order_payload_reference",
    "risk_gate_reference",
    "execution_router_reference",
    "runtime_resolver_snapshot_reference",
    "order_intent_contract_reference",
    "connector_capability_reference",
    "venue_write_connectivity_reference",
    "live_signer_path_reference",
    "final_order_release_reference",
}

FALSE_SURFACE_FIELDS = {
    "contains_runtime_resolver_snapshot",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_runtime_cash_receipt",
    "order_intent_runtime_allowed",
    "order_execution_allowed",
    "order_submission_allowed",
    "final_order_release_allowed",
    "contains_order_instruction",
    "contains_order_receipt",
    "contains_order_submission_payload",
    "contains_accepted_source_fact",
    "gate_evaluation_allowed",
    "final_order_submission_authority_present",
    "order_cancel_allowed",
    "order_reduce_allowed",
    "order_close_allowed",
    "order_replace_allowed",
    "order_amend_allowed",
    "live_signer_path_present",
    "venue_write_connectivity_present",
}

ORDER_INTENT_PLACEHOLDER_FIELDS = {
    "intent_contract_type",
    "intent_contract_id",
    "schema_state",
    "intent_state",
    "semantic_binding_state",
    "runtime_state",
    "source_required_order_intent_fields",
    "venue_reference",
    "market_reference",
    "contract_reference",
    "event_reference",
    "connector_reference",
    "order_payload_reference",
    "risk_gate_reference",
    "execution_router_reference",
    "order_intent_runtime_allowed",
    "order_execution_allowed",
    "order_submission_allowed",
    "final_order_release_allowed",
    "contains_order_instruction",
    "contains_order_receipt",
    "contains_order_submission_payload",
    "contains_accepted_source_fact",
}

ROUTER_GATE_PLACEHOLDER_FIELDS = {
    "router_contract_type",
    "router_contract_id",
    "router_state",
    "semantic_binding_state",
    "runtime_state",
    "source_required_order_intent_fields",
    "order_intent_contract_reference",
    "risk_gate_reference",
    "connector_capability_reference",
    "venue_reference",
    "venue_write_connectivity_reference",
    "live_signer_path_reference",
    "final_order_release_reference",
    "gate_evaluation_allowed",
    "final_order_submission_authority_present",
    "final_order_release_allowed",
    "order_execution_allowed",
    "order_submission_allowed",
    "order_cancel_allowed",
    "order_reduce_allowed",
    "order_close_allowed",
    "order_replace_allowed",
    "order_amend_allowed",
    "live_signer_path_present",
    "venue_write_connectivity_present",
    "contains_order_instruction",
    "contains_order_receipt",
}

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "mode",
    "execution",
    "schema_authority_class",
    "surface_kind",
    "deterministic_output",
    "runtime_resolver_snapshot_reference",
    "contains_runtime_resolver_snapshot",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_runtime_cash_receipt",
    "scope_flags",
    "forbidden_action_flags",
    "fixture_no_claim_flags",
    "order_intent_placeholders",
    "execution_router_gate_placeholders",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR25_ORDER_INTENT_EXECUTION_ROUTER_SCAFFOLD_FIXTURE",
    "fixture_version": "PR25_ORDER_INTENT_EXECUTION_ROUTER_FIXTURE_V1",
    "fixture_authority_class": "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ORDER_AUTHORITY_NOT_SOURCE_FACT",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "schema_authority_class": "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ORDER_EXECUTION_AUTHORITY",
    "surface_kind": "ORDER_INTENT_EXECUTION_ROUTER_STATIC_SCAFFOLD",
    "deterministic_output": True,
    "runtime_resolver_snapshot_reference": "UNBOUND",
    "contains_runtime_resolver_snapshot": False,
    "contains_replay_result_packet": False,
    "contains_paper_result_packet": False,
    "contains_runtime_cash_receipt": False,
}

EXPECTED_SCHEMA_DEFS = {
    "record_id",
    "source_required",
    "unbound",
    "disabled",
    "scope_flags",
    "forbidden_action_flags",
    "fixture_no_claim_flags",
    "source_required_order_semantics",
    "order_intent_placeholder",
    "execution_router_gate_placeholder",
}

ALLOWED_SCAFFOLD_IDENTIFIERS = {
    "SYNTHETIC_PR25_ORDER_INTENT_EXECUTION_ROUTER_SCAFFOLD_FIXTURE",
    "PR25_ORDER_INTENT_EXECUTION_ROUTER_FIXTURE_V1",
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ORDER_AUTHORITY_NOT_SOURCE_FACT",
    "SOURCE_REQUIRED",
    "DISABLED",
    "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ORDER_EXECUTION_AUTHORITY",
    "ORDER_INTENT_EXECUTION_ROUTER_STATIC_SCAFFOLD",
    "UNBOUND",
    "VENUE_NEUTRAL_ORDER_INTENT_PLACEHOLDER_CONTRACT",
    "SYNTHETIC_PR25_ORDER_INTENT_PLACEHOLDER",
    "SCAFFOLD_ONLY",
    "PLACEHOLDER_ONLY_NOT_RUNTIME_INTENT",
    "EXECUTION_ROUTER_GATE_PLACEHOLDER_CONTRACT",
    "SYNTHETIC_PR25_EXECUTION_ROUTER_GATE_PLACEHOLDER",
    "GATE_PLACEHOLDER_ONLY_NOT_EXECUTABLE",
    "ORDER_INTENT_EXECUTION_ROUTER_STATIC_VALIDATION_ONLY",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "kalshi",
    "polymarket",
    "forecastx",
    "forecastex",
    "ibkr",
    "http",
    "https",
    "api",
    "endpoint",
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


def _require_fields(value: dict[str, Any], fields: set[str], label: str) -> list[str]:
    missing = sorted(fields - set(value))
    if missing:
        return [f"{label} missing required fields: {', '.join(missing)}"]
    return []


def _require_exact_fields(value: dict[str, Any], fields: set[str], label: str) -> list[str]:
    failures = _require_fields(value, fields, label)
    unexpected = sorted(set(value) - fields)
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


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


def _validate_schema_object_contract(
    definition: dict[str, Any],
    *,
    expected_fields: set[str],
    label: str,
    require_additional_properties_false: bool = True,
) -> list[str]:
    failures: list[str] = []
    if definition.get("type") != "object":
        failures.append(f"{label}.type must be object")
    if require_additional_properties_false and definition.get("additionalProperties") is not False:
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


def _mapping(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _non_empty_list(value: dict[str, Any], field: str, label: str) -> tuple[list[Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, list) or not item:
        return None, [f"{label}.{field} must be a non-empty list"]
    return item, []


def _validate_false_map(
    value: dict[str, Any], expected_fields: set[str], label: str
) -> list[str]:
    failures = _require_exact_fields(value, expected_fields, label)
    for field in sorted(expected_fields):
        if field in value and value[field] is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def _validate_scope_flags(fixture: dict[str, Any]) -> list[str]:
    scope_flags, failures = _mapping(fixture, "scope_flags", "order intent fixture")
    if scope_flags is None:
        return failures
    failures.extend(
        _require_exact_fields(
            scope_flags,
            TRUE_SCOPE_FLAGS | FALSE_SCOPE_FLAGS,
            "scope_flags",
        )
    )
    for field in sorted(TRUE_SCOPE_FLAGS):
        if field in scope_flags and scope_flags[field] is not True:
            failures.append(f"scope_flags.{field} must be true")
    for field in sorted(FALSE_SCOPE_FLAGS):
        if field in scope_flags and scope_flags[field] is not False:
            failures.append(f"scope_flags.{field} must be false")
    return failures


def _validate_schema(schema: dict[str, Any]) -> list[str]:
    failures = _require_fields(
        schema,
        {"$schema", "$id", "type", "properties", "required", "$defs"},
        "schema",
    )
    if schema.get("type") != "object":
        failures.append("schema.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")

    properties = schema.get("properties")
    required = schema.get("required")
    defs = schema.get("$defs")

    if isinstance(properties, dict):
        failures.extend(_require_exact_fields(properties, ROOT_FIELDS, "schema.properties"))
        for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
            prop = properties.get(field, {})
            if not isinstance(prop, dict) or prop.get("const") != expected:
                failures.append(f"schema.properties.{field} must be const {expected}")
        expected_refs = {
            "scope_flags": "#/$defs/scope_flags",
            "forbidden_action_flags": "#/$defs/forbidden_action_flags",
            "fixture_no_claim_flags": "#/$defs/fixture_no_claim_flags",
        }
        for field, expected_ref in sorted(expected_refs.items()):
            prop = properties.get(field, {})
            if not isinstance(prop, dict) or prop.get("$ref") != expected_ref:
                failures.append(f"schema.properties.{field} must reference {expected_ref}")
    else:
        failures.append("schema.properties must be an object")

    if isinstance(required, list):
        required_fields = set(required)
        missing_required = sorted(ROOT_FIELDS - required_fields)
        unexpected_required = sorted(required_fields - ROOT_FIELDS)
        if missing_required:
            failures.append(f"schema root missing required fields: {', '.join(missing_required)}")
        if unexpected_required:
            failures.append(f"schema root has unexpected required fields: {', '.join(unexpected_required)}")
        if len(required) != len(required_fields):
            failures.append("schema.required must not contain duplicate fields")
    else:
        failures.append("schema.required must be a list")

    if isinstance(defs, dict):
        failures.extend(_require_fields(defs, EXPECTED_SCHEMA_DEFS, "schema.$defs"))
        if "false_flag_map" in defs:
            failures.append("schema.$defs.false_flag_map must not exist; flags must be explicit")

        if isinstance(defs.get("source_required"), dict) and defs["source_required"].get("const") != "SOURCE_REQUIRED":
            failures.append("schema.$defs.source_required must be const SOURCE_REQUIRED")
        if isinstance(defs.get("unbound"), dict) and defs["unbound"].get("const") != "UNBOUND":
            failures.append("schema.$defs.unbound must be const UNBOUND")
        if isinstance(defs.get("disabled"), dict) and defs["disabled"].get("const") != "DISABLED":
            failures.append("schema.$defs.disabled must be const DISABLED")

        scope_definition = defs.get("scope_flags")
        if isinstance(scope_definition, dict):
            failures.extend(
                _validate_boolean_const_schema(
                    scope_definition,
                    expected={
                        **{field: True for field in TRUE_SCOPE_FLAGS},
                        **{field: False for field in FALSE_SCOPE_FLAGS},
                    },
                    label="schema.$defs.scope_flags",
                )
            )
        else:
            failures.append("schema.$defs.scope_flags must be an object")

        forbidden_flags = defs.get("forbidden_action_flags")
        if isinstance(forbidden_flags, dict):
            failures.extend(
                _validate_boolean_const_schema(
                    forbidden_flags,
                    expected={field: False for field in FORBIDDEN_ACTION_FLAGS},
                    label="schema.$defs.forbidden_action_flags",
                )
            )
        else:
            failures.append("schema.$defs.forbidden_action_flags must be an object")

        no_claim_flags = defs.get("fixture_no_claim_flags")
        if isinstance(no_claim_flags, dict):
            failures.extend(
                _validate_boolean_const_schema(
                    no_claim_flags,
                    expected={field: False for field in NO_CLAIM_FLAGS},
                    label="schema.$defs.fixture_no_claim_flags",
                )
            )
        else:
            failures.append("schema.$defs.fixture_no_claim_flags must be an object")

        semantics = defs.get("source_required_order_semantics")
        if isinstance(semantics, dict):
            failures.extend(
                _validate_schema_object_contract(
                    semantics,
                    expected_fields=SEMANTIC_FIELDS,
                    label="schema.$defs.source_required_order_semantics",
                )
            )
            for field in sorted(SEMANTIC_FIELDS):
                if _ref_value(semantics, field) != "#/$defs/source_required":
                    failures.append(
                        "schema.$defs.source_required_order_semantics."
                        f"{field} must reference #/$defs/source_required"
                    )
        else:
            failures.append("schema.$defs.source_required_order_semantics must be an object")

        intent = defs.get("order_intent_placeholder")
        if isinstance(intent, dict):
            failures.extend(
                _validate_schema_object_contract(
                    intent,
                    expected_fields=ORDER_INTENT_PLACEHOLDER_FIELDS,
                    label="schema.$defs.order_intent_placeholder",
                )
            )
            expected_consts = {
                "intent_contract_type": "VENUE_NEUTRAL_ORDER_INTENT_PLACEHOLDER_CONTRACT",
                "schema_state": "SCAFFOLD_ONLY",
                "intent_state": "PLACEHOLDER_ONLY_NOT_RUNTIME_INTENT",
            }
            for field, expected in sorted(expected_consts.items()):
                if _const_value(intent, field) != expected:
                    failures.append(
                        f"schema.$defs.order_intent_placeholder.{field} must be const {expected}"
                    )
            for field in sorted(
                {
                    "semantic_binding_state",
                    "venue_reference",
                    "market_reference",
                    "contract_reference",
                    "event_reference",
                    "connector_reference",
                    "order_payload_reference",
                    "risk_gate_reference",
                    "execution_router_reference",
                }
            ):
                if _ref_value(intent, field) != "#/$defs/unbound":
                    failures.append(
                        f"schema.$defs.order_intent_placeholder.{field} must reference #/$defs/unbound"
                    )
            if _ref_value(intent, "runtime_state") != "#/$defs/disabled":
                failures.append("schema.$defs.order_intent_placeholder.runtime_state must reference #/$defs/disabled")
            if _ref_value(intent, "source_required_order_intent_fields") != "#/$defs/source_required_order_semantics":
                failures.append(
                    "schema.$defs.order_intent_placeholder.source_required_order_intent_fields "
                    "must reference #/$defs/source_required_order_semantics"
                )
            for field in sorted(ORDER_INTENT_PLACEHOLDER_FIELDS & FALSE_SURFACE_FIELDS):
                if _const_value(intent, field) is not False:
                    failures.append(
                        f"schema.$defs.order_intent_placeholder.{field} must be const false"
                    )
        else:
            failures.append("schema.$defs.order_intent_placeholder must be an object")

        gate = defs.get("execution_router_gate_placeholder")
        if isinstance(gate, dict):
            failures.extend(
                _validate_schema_object_contract(
                    gate,
                    expected_fields=ROUTER_GATE_PLACEHOLDER_FIELDS,
                    label="schema.$defs.execution_router_gate_placeholder",
                )
            )
            expected_consts = {
                "router_contract_type": "EXECUTION_ROUTER_GATE_PLACEHOLDER_CONTRACT",
                "router_state": "GATE_PLACEHOLDER_ONLY_NOT_EXECUTABLE",
            }
            for field, expected in sorted(expected_consts.items()):
                if _const_value(gate, field) != expected:
                    failures.append(
                        f"schema.$defs.execution_router_gate_placeholder.{field} must be const {expected}"
                    )
            for field in sorted(
                {
                    "semantic_binding_state",
                    "order_intent_contract_reference",
                    "risk_gate_reference",
                    "connector_capability_reference",
                    "venue_reference",
                    "venue_write_connectivity_reference",
                    "live_signer_path_reference",
                    "final_order_release_reference",
                }
            ):
                if _ref_value(gate, field) != "#/$defs/unbound":
                    failures.append(
                        "schema.$defs.execution_router_gate_placeholder."
                        f"{field} must reference #/$defs/unbound"
                    )
            if _ref_value(gate, "runtime_state") != "#/$defs/disabled":
                failures.append(
                    "schema.$defs.execution_router_gate_placeholder.runtime_state "
                    "must reference #/$defs/disabled"
                )
            if _ref_value(gate, "source_required_order_intent_fields") != "#/$defs/source_required_order_semantics":
                failures.append(
                    "schema.$defs.execution_router_gate_placeholder.source_required_order_intent_fields "
                    "must reference #/$defs/source_required_order_semantics"
                )
            for field in sorted(ROUTER_GATE_PLACEHOLDER_FIELDS & FALSE_SURFACE_FIELDS):
                if _const_value(gate, field) is not False:
                    failures.append(
                        f"schema.$defs.execution_router_gate_placeholder.{field} must be const false"
                    )
        else:
            failures.append("schema.$defs.execution_router_gate_placeholder must be an object")
    else:
        failures.append("schema.$defs must be an object")

    return failures


def _validate_order_intent_placeholder(surface: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(surface, ORDER_INTENT_PLACEHOLDER_FIELDS, label)
    if surface.get("intent_contract_type") != "VENUE_NEUTRAL_ORDER_INTENT_PLACEHOLDER_CONTRACT":
        failures.append(f"{label}.intent_contract_type must remain venue-neutral placeholder")
    if surface.get("schema_state") != "SCAFFOLD_ONLY":
        failures.append(f"{label}.schema_state must be SCAFFOLD_ONLY")
    if surface.get("intent_state") != "PLACEHOLDER_ONLY_NOT_RUNTIME_INTENT":
        failures.append(f"{label}.intent_state must remain placeholder-only")
    if surface.get("semantic_binding_state") != "UNBOUND":
        failures.append(f"{label}.semantic_binding_state must be UNBOUND")
    if surface.get("runtime_state") != "DISABLED":
        failures.append(f"{label}.runtime_state must be DISABLED")
    semantics, semantic_failures = _mapping(surface, "source_required_order_intent_fields", label)
    failures.extend(semantic_failures)
    if semantics is not None:
        failures.extend(
            _require_exact_fields(
                semantics,
                SEMANTIC_FIELDS,
                f"{label}.source_required_order_intent_fields",
            )
        )
        for field in sorted(SEMANTIC_FIELDS):
            if semantics.get(field) != "SOURCE_REQUIRED":
                failures.append(
                    f"{label}.source_required_order_intent_fields.{field} "
                    "must be SOURCE_REQUIRED"
                )
    return failures


def _validate_router_gate_placeholder(surface: dict[str, Any], label: str) -> list[str]:
    failures = _require_exact_fields(surface, ROUTER_GATE_PLACEHOLDER_FIELDS, label)
    if surface.get("router_contract_type") != "EXECUTION_ROUTER_GATE_PLACEHOLDER_CONTRACT":
        failures.append(f"{label}.router_contract_type must remain gate placeholder")
    if surface.get("router_state") != "GATE_PLACEHOLDER_ONLY_NOT_EXECUTABLE":
        failures.append(f"{label}.router_state must remain not executable")
    if surface.get("semantic_binding_state") != "UNBOUND":
        failures.append(f"{label}.semantic_binding_state must be UNBOUND")
    if surface.get("runtime_state") != "DISABLED":
        failures.append(f"{label}.runtime_state must be DISABLED")
    semantics, semantic_failures = _mapping(surface, "source_required_order_intent_fields", label)
    failures.extend(semantic_failures)
    if semantics is not None:
        failures.extend(
            _require_exact_fields(
                semantics,
                SEMANTIC_FIELDS,
                f"{label}.source_required_order_intent_fields",
            )
        )
        for field in sorted(SEMANTIC_FIELDS):
            if semantics.get(field) != "SOURCE_REQUIRED":
                failures.append(
                    f"{label}.source_required_order_intent_fields.{field} "
                    "must be SOURCE_REQUIRED"
                )
    return failures


def _validate_global_fail_closed_values(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = FORBIDDEN_ACTION_FLAGS | NO_CLAIM_FLAGS | FALSE_SCOPE_FLAGS | FALSE_SURFACE_FIELDS
    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in SEMANTIC_FIELDS and item != "SOURCE_REQUIRED":
            failures.append(f"{path} must remain SOURCE_REQUIRED")
        if key in UNBOUND_REFERENCE_FIELDS and item != "UNBOUND":
            failures.append(f"{path} must remain UNBOUND")
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime or venue values")
        if isinstance(item, str) and item not in ALLOWED_SCAFFOLD_IDENTIFIERS:
            lowered = item.lower()
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_order_intent_execution_router_fixture(fixture: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "order intent fixture")
    for field, value in ROOT_CONST_EXPECTATIONS.items():
        if fixture.get(field) != value:
            failures.append(f"order intent fixture.{field} must be {value}")

    failures.extend(_validate_scope_flags(fixture))
    action_flags, action_failures = _mapping(fixture, "forbidden_action_flags", "order intent fixture")
    failures.extend(action_failures)
    if action_flags is not None:
        failures.extend(_validate_false_map(action_flags, FORBIDDEN_ACTION_FLAGS, "forbidden_action_flags"))
    no_claim_flags, no_claim_failures = _mapping(fixture, "fixture_no_claim_flags", "order intent fixture")
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(_validate_false_map(no_claim_flags, NO_CLAIM_FLAGS, "fixture_no_claim_flags"))

    intents, intent_failures = _non_empty_list(fixture, "order_intent_placeholders", "order intent fixture")
    failures.extend(intent_failures)
    for index, item in enumerate(intents or []):
        if isinstance(item, dict):
            failures.extend(_validate_order_intent_placeholder(item, f"order_intent_placeholders[{index}]"))
        else:
            failures.append(f"order_intent_placeholders[{index}] must be an object")

    gates, gate_failures = _non_empty_list(fixture, "execution_router_gate_placeholders", "order intent fixture")
    failures.extend(gate_failures)
    for index, item in enumerate(gates or []):
        if isinstance(item, dict):
            failures.extend(_validate_router_gate_placeholder(item, f"execution_router_gate_placeholders[{index}]"))
        else:
            failures.append(f"execution_router_gate_placeholders[{index}] must be an object")

    failures.extend(_validate_global_fail_closed_values(fixture))
    return failures


def validate_static_surface(*, schema_path: pathlib.Path, fixture_path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    schema, schema_failures = _load_json(schema_path)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)
    if schema is not None:
        failures.extend(_validate_schema(schema))
    if fixture is not None:
        failures.extend(validate_order_intent_execution_router_fixture(fixture))
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
            "ORDER_INTENT_EXECUTION_ROUTER_STATIC_VALIDATION_FAILED\n- "
            + "\n- ".join(failures)
        )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
