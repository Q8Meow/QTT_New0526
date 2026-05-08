#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "RUNTIME_ORCHESTRATION_STATIC_VALIDATION_OK"

RUNTIME_AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "source_required": True,
    "execution_disabled": True,
    "scaffold_only": True,
    "deterministic_static_fixture_only": True,
    "synthetic_records_only": True,
    "accepted_source_evidence_required_before_runtime_use": True,
    "accepted_source_evidence_present": False,
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
    "private_state_fetch_allowed": False,
    "runtime_cash_fetch_allowed": False,
    "runtime_cash_receipt_creation_allowed": False,
    "order_execution_allowed": False,
    "profit_claim_allowed": False,
    "network_io_allowed": False,
    "atomicrows_bundle_creation_allowed": False,
    "sha_freeze_authority_allowed": False,
    "blocker_reduction_allowed": False,
}

RUNTIME_FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "accepted_source_packet_creation_enabled",
    "connector_binding_enabled",
    "semantic_value_population_enabled",
    "runtime_enabled",
    "runtime_execution_enabled",
    "runtime_trading_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "replay_paper_execution_enabled",
    "replay_result_packet_creation_enabled",
    "paper_result_packet_creation_enabled",
    "live_enabled",
    "live_reachability_enabled",
    "private_state_fetch_enabled",
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

RUNTIME_NO_CLAIM_AUTHORITY_FIELDS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "connector_semantic_value_authority",
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
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "order_execution_allowed",
    "atomicrows_bundle_creation_allowed",
    "sha_freeze_authority_allowed",
    "blocker_reduction_allowed",
    "profit_claim_allowed",
}

RECEIPT_FALSE_FIELDS = {
    "contains_runtime_result",
    "contains_runtime_resolver_snapshot",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_runtime_cash_receipt",
    "contains_order_receipt",
    "contains_accepted_source_fact",
}

STATE_AND_GATE_FALSE_FIELDS = {
    "state_execution_allowed",
    "entry_action_allowed",
    "exit_action_allowed",
    "opens_runtime_path",
    "opens_live_path",
    "opens_order_path",
    "transition_execution_allowed",
    "live_transition_allowed",
    "order_transition_allowed",
    "gate_evaluation_allowed",
}

FIXTURE_NO_CLAIM_FIELDS = {
    "contains_real_contract_identifier",
    "contains_real_event_identifier",
    "contains_real_venue_identifier",
    "contains_real_market_identifier",
    "contains_real_connector_identifier",
    "contains_credentials",
    "contains_real_url",
    "contains_accepted_source_facts",
    "contains_connector_semantic_values",
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

REQUIRED_SURFACE_DEFS = {
    "runtime_authority_scope_flags": set(RUNTIME_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
    "runtime_forbidden_action_flags": RUNTIME_FORBIDDEN_ACTION_FLAGS,
    "no_claim_flags": RUNTIME_NO_CLAIM_AUTHORITY_FIELDS,
    "receipt_envelope_placeholder": {
        "receipt_envelope_type",
        "receipt_id",
        "receipt_state",
        "mode",
        "execution",
        "scaffold_state",
        "contains_runtime_result",
        "contains_runtime_resolver_snapshot",
        "contains_replay_result_packet",
        "contains_paper_result_packet",
        "contains_runtime_cash_receipt",
        "contains_order_receipt",
        "contains_accepted_source_fact",
        "source_reference",
        "runtime_resolver_snapshot_reference",
        "replay_result_reference",
        "paper_result_reference",
        "runtime_cash_receipt_reference",
        "order_receipt_reference",
        "runtime_authority_scope_flags",
        "runtime_forbidden_action_flags",
        "no_claim_flags",
    },
    "state_placeholder": {
        "state_id",
        "state_status",
        "state_execution_allowed",
        "entry_action_allowed",
        "exit_action_allowed",
        "opens_runtime_path",
        "opens_live_path",
        "opens_order_path",
        "source_required",
        "accepted_source_evidence_present",
    },
    "state_machine_placeholder": {
        "state_machine_type",
        "state_machine_id",
        "state_machine_state",
        "initial_state",
        "terminal_state",
        "transition_execution_allowed",
        "runtime_execution_allowed",
        "live_transition_allowed",
        "order_transition_allowed",
        "state_placeholders",
        "runtime_authority_scope_flags",
        "runtime_forbidden_action_flags",
        "no_claim_flags",
    },
    "gate_placeholder": {
        "gate_type",
        "gate_id",
        "gate_state",
        "gate_result_state",
        "gate_evaluation_allowed",
        "opens_runtime_path",
        "opens_live_path",
        "opens_order_path",
        "required_before_runtime",
        "source_required",
        "accepted_source_evidence_present",
        "runtime_authority_scope_flags",
        "runtime_forbidden_action_flags",
        "no_claim_flags",
    },
    "runtime_orchestration_skeleton": {
        "skeleton_type",
        "skeleton_id",
        "skeleton_authority_class",
        "mode",
        "execution",
        "scaffold_state",
        "deterministic_output",
        "runtime_authority_scope_flags",
        "runtime_forbidden_action_flags",
        "receipt_envelopes",
        "state_machine_placeholders",
        "gate_placeholders",
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
    "runtime_orchestration_skeleton",
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
        set(RUNTIME_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
        label,
    )
    for field, expected in sorted(RUNTIME_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
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
        RUNTIME_FORBIDDEN_ACTION_FLAGS
        | RUNTIME_NO_CLAIM_AUTHORITY_FIELDS
        | ROOT_DISABLED_GUARDRAIL_FIELDS
        | RECEIPT_FALSE_FIELDS
        | STATE_AND_GATE_FALSE_FIELDS
        | FIXTURE_NO_CLAIM_FIELDS
        | {
            "accepted_source_evidence_present",
            "contains_accepted_source_fact",
            "contains_runtime_result",
            "contains_runtime_resolver_snapshot",
            "contains_replay_result_packet",
            "contains_paper_result_packet",
            "contains_runtime_cash_receipt",
            "contains_order_receipt",
        }
    )
    for path, key, item in _walk_values(value):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
    return failures


def _validate_no_forbidden_text(value: dict[str, Any]) -> list[str]:
    raw_text = json.dumps(value, sort_keys=True).lower()
    return [
        f"fixture contains forbidden runtime/live/source fragment: {fragment}"
        for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS)
        if fragment in raw_text
    ]


def _validate_synthetic_references(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk_values(value):
        if key.endswith("_reference") and isinstance(item, str):
            if item == "SOURCE_REQUIRED_NO_ACCEPTED_SOURCE_EVIDENCE":
                continue
            if not item.startswith("SYNTHETIC_"):
                failures.append(f"{path} must remain a synthetic/source-required reference")
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime values")
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
        "runtime_orchestration_skeleton",
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
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_RUNTIME_ORCHESTRATION_AUTHORITY"
    ):
        failures.append("schema root authority class must be static non-runtime")
    if _const_value(schema, "surface_kind") != (
        "RUNTIME_ORCHESTRATION_SKELETON_STATIC_SCAFFOLD"
    ):
        failures.append("schema root surface kind must be runtime orchestration scaffold")

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
        for field in sorted(RUNTIME_NO_CLAIM_AUTHORITY_FIELDS):
            if _const_value(no_claim_def, field) is not False:
                failures.append(f"no_claim_flags must set {field} to const false")

    action_def = defs.get("runtime_forbidden_action_flags")
    if isinstance(action_def, dict):
        for field in sorted(RUNTIME_FORBIDDEN_ACTION_FLAGS):
            if _const_value(action_def, field) is not False:
                failures.append(f"runtime forbidden flag {field} must be const false")

    scope_def = defs.get("runtime_authority_scope_flags")
    if isinstance(scope_def, dict):
        for field, expected in sorted(RUNTIME_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
            if _const_value(scope_def, field) is not expected:
                failures.append(f"runtime authority/scope flag {field} must be const {expected}")

    return failures


def _validate_scope_and_action_maps(owner: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    scope_flags, scope_failures = _mapping_at(owner, "runtime_authority_scope_flags", label)
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(_validate_authority_scope_flag_map(scope_flags, f"{label}.runtime_authority_scope_flags"))

    action_flags, action_failures = _mapping_at(owner, "runtime_forbidden_action_flags", label)
    failures.extend(action_failures)
    if action_flags is not None:
        failures.extend(_validate_false_flag_map(action_flags, RUNTIME_FORBIDDEN_ACTION_FLAGS, f"{label}.runtime_forbidden_action_flags"))

    no_claim_flags, no_claim_failures = _mapping_at(owner, "no_claim_flags", label)
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(_validate_false_flag_map(no_claim_flags, RUNTIME_NO_CLAIM_AUTHORITY_FIELDS, f"{label}.no_claim_flags"))
    return failures


def validate_runtime_orchestration_skeleton_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _require_mapping_fields(
            fixture,
            FIXTURE_REQUIRED_ROOT_FIELDS,
            "runtime orchestration fixture",
        )
    )

    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_RUNTIME_ORCHESTRATION_NOT_SOURCE_FACT"
    ):
        failures.append("runtime orchestration fixture must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
    ):
        failures.append("runtime orchestration fixture example authority must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("runtime orchestration fixture mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("runtime orchestration fixture execution must be DISABLED")
    if fixture.get("schema_authority_class") != (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_RUNTIME_ORCHESTRATION_AUTHORITY"
    ):
        failures.append("runtime orchestration fixture schema authority must be static-only")
    if fixture.get("surface_kind") != "RUNTIME_ORCHESTRATION_SKELETON_STATIC_SCAFFOLD":
        failures.append("runtime orchestration fixture surface kind must be skeleton scaffold")
    if fixture.get("deterministic_output") is not True:
        failures.append("runtime orchestration fixture deterministic_output must be true")

    fixture_no_claim_flags, fixture_flag_failures = _mapping_at(
        fixture, "fixture_no_claim_flags", "runtime orchestration fixture"
    )
    failures.extend(fixture_flag_failures)
    if fixture_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                fixture_no_claim_flags,
                FIXTURE_NO_CLAIM_FIELDS,
                "runtime orchestration fixture.fixture_no_claim_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(
        fixture, "no_claim_flags", "runtime orchestration fixture"
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                RUNTIME_NO_CLAIM_AUTHORITY_FIELDS,
                "runtime orchestration fixture.no_claim_flags",
            )
        )

    skeleton, skeleton_failures = _mapping_at(
        fixture,
        "runtime_orchestration_skeleton",
        "runtime orchestration fixture",
    )
    failures.extend(skeleton_failures)
    if skeleton is None:
        return failures

    skeleton_label = "runtime_orchestration_skeleton"
    failures.extend(
        _require_mapping_fields(
            skeleton,
            REQUIRED_SURFACE_DEFS["runtime_orchestration_skeleton"],
            skeleton_label,
        )
    )
    if skeleton.get("skeleton_type") != "RUNTIME_ORCHESTRATION_SKELETON_STATIC_SCAFFOLD":
        failures.append("runtime_orchestration_skeleton.skeleton_type must be static scaffold")
    if skeleton.get("skeleton_authority_class") != (
        "STATIC_RUNTIME_ORCHESTRATION_SKELETON_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append("runtime_orchestration_skeleton authority class must be static-only")
    if skeleton.get("mode") != "SOURCE_REQUIRED":
        failures.append("runtime_orchestration_skeleton mode must be SOURCE_REQUIRED")
    if skeleton.get("execution") != "DISABLED":
        failures.append("runtime_orchestration_skeleton execution must be DISABLED")
    if skeleton.get("scaffold_state") != "SCAFFOLD_ONLY":
        failures.append("runtime_orchestration_skeleton scaffold_state must be SCAFFOLD_ONLY")
    if skeleton.get("deterministic_output") is not True:
        failures.append("runtime_orchestration_skeleton deterministic_output must be true")
    failures.extend(_validate_scope_and_action_maps(skeleton, skeleton_label))

    receipts, receipt_failures = _list_at(
        skeleton, "receipt_envelopes", skeleton_label
    )
    failures.extend(receipt_failures)
    if receipts is not None:
        for index, receipt in enumerate(receipts):
            label = f"{skeleton_label}.receipt_envelopes[{index}]"
            if not isinstance(receipt, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_mapping_fields(
                    receipt,
                    REQUIRED_SURFACE_DEFS["receipt_envelope_placeholder"],
                    label,
                )
            )
            failures.extend(_validate_scope_and_action_maps(receipt, label))
            failures.extend(_validate_false_flag_map(receipt, RECEIPT_FALSE_FIELDS, label))

    state_machines, state_machine_failures = _list_at(
        skeleton, "state_machine_placeholders", skeleton_label
    )
    failures.extend(state_machine_failures)
    if state_machines is not None:
        for index, state_machine in enumerate(state_machines):
            label = f"{skeleton_label}.state_machine_placeholders[{index}]"
            if not isinstance(state_machine, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_mapping_fields(
                    state_machine,
                    REQUIRED_SURFACE_DEFS["state_machine_placeholder"],
                    label,
                )
            )
            failures.extend(_validate_scope_and_action_maps(state_machine, label))
            if state_machine.get("state_machine_state") != "SCAFFOLD_ONLY_NOT_EXECUTABLE":
                failures.append(f"{label}.state_machine_state must be scaffold-only")
            states, state_failures = _list_at(state_machine, "state_placeholders", label)
            failures.extend(state_failures)
            if states is not None:
                for state_index, state in enumerate(states):
                    state_label = f"{label}.state_placeholders[{state_index}]"
                    if not isinstance(state, dict):
                        failures.append(f"{state_label} must be an object")
                        continue
                    failures.extend(
                        _require_mapping_fields(
                            state,
                            REQUIRED_SURFACE_DEFS["state_placeholder"],
                            state_label,
                        )
                    )
                    if state.get("state_status") != "SCAFFOLD_ONLY_NOT_EXECUTABLE":
                        failures.append(f"{state_label}.state_status must be scaffold-only")

    gates, gate_failures = _list_at(skeleton, "gate_placeholders", skeleton_label)
    failures.extend(gate_failures)
    if gates is not None:
        for index, gate in enumerate(gates):
            label = f"{skeleton_label}.gate_placeholders[{index}]"
            if not isinstance(gate, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(
                _require_mapping_fields(
                    gate,
                    REQUIRED_SURFACE_DEFS["gate_placeholder"],
                    label,
                )
            )
            failures.extend(_validate_scope_and_action_maps(gate, label))
            if gate.get("gate_state") != "SOURCE_REQUIRED_DISABLED":
                failures.append(f"{label}.gate_state must be SOURCE_REQUIRED_DISABLED")
            if gate.get("gate_result_state") != "NOT_EVALUATED_NO_RUNTIME_AUTHORITY":
                failures.append(f"{label}.gate_result_state must remain unevaluated")

    failures.extend(_validate_no_forbidden_true_values(fixture))
    failures.extend(_validate_no_forbidden_text(fixture))
    failures.extend(_validate_synthetic_references(fixture))
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
        failures.extend(validate_runtime_orchestration_skeleton_fixture(fixture))

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
            "RUNTIME_ORCHESTRATION_STATIC_VALIDATION_FAILED\n- "
            + "\n- ".join(failures)
        )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
