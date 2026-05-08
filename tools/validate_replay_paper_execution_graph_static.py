#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "REPLAY_PAPER_EXECUTION_GRAPH_STATIC_VALIDATION_OK"

EXECUTION_GRAPH_AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "source_required": True,
    "execution_disabled": True,
    "scaffold_only": True,
    "deterministic_static_fixture_only": True,
    "synthetic_records_only": True,
    "accepted_source_evidence_required_before_runtime_use": True,
    "accepted_source_evidence_present": False,
    "runtime_resolver_snapshot_required_before_graph_use": True,
    "runtime_resolver_snapshot_present": False,
    "shared_input_identity_required_before_lanes": True,
    "immutable_input_lock_required_before_lanes": True,
    "lane_separation_required": True,
    "result_packet_boundaries_placeholder_only": True,
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
    "dual_result_review_allowed": False,
    "live_use_allowed": False,
    "live_eligibility_creation_allowed": False,
    "live_reachability_allowed": False,
    "private_state_fetch_allowed": False,
    "runtime_cash_fetch_allowed": False,
    "runtime_cash_receipt_creation_allowed": False,
    "order_execution_allowed": False,
    "network_io_allowed": False,
    "atomicrows_bundle_creation_allowed": False,
    "sha_freeze_authority_allowed": False,
    "blocker_reduction_allowed": False,
    "profit_claim_allowed": False,
}

EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS = {
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
    "runtime_resolver_snapshot_materialization_enabled",
    "shared_input_identity_digest_computation_enabled",
    "immutable_input_lock_materialization_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "replay_paper_execution_enabled",
    "replay_result_packet_creation_enabled",
    "paper_result_packet_creation_enabled",
    "real_replay_result_packet_claimed",
    "real_paper_result_packet_claimed",
    "dual_result_review_enabled",
    "live_eligibility_creation_enabled",
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

NO_CLAIM_AUTHORITY_FIELDS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "connector_semantic_value_authority",
    "runtime_authority",
    "runtime_execution_authority",
    "runtime_trading_authority",
    "replay_paper_execution_graph_authority",
    "runtime_resolver_snapshot_authority",
    "shared_input_identity_runtime_authority",
    "immutable_input_lock_runtime_authority",
    "replay_execution_authority",
    "paper_execution_authority",
    "replay_result_packet_authority",
    "paper_result_packet_authority",
    "dual_result_review_authority",
    "live_eligibility_authority",
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
    "contains_credentials",
    "contains_real_url",
    "contains_accepted_source_facts",
    "contains_connector_semantic_values",
    "contains_private_state",
    "contains_balance_value",
    "contains_position_value",
    "contains_open_orders",
    "contains_runtime_resolver_snapshot",
    "contains_real_shared_input_identity",
    "contains_computed_input_identity_digest",
    "contains_materialized_input_lock",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_dual_result_review_packet",
    "contains_live_eligibility",
    "contains_live_reachability",
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
    "creates_shared_input_identity_digest",
    "materializes_input_lock",
    "executes_replay",
    "executes_paper",
    "creates_replay_result",
    "creates_paper_result",
    "creates_dual_result_review",
    "creates_live_eligibility",
    "creates_runtime_cash_receipts",
    "executes_orders",
    "cancels_orders",
    "reduces_or_closes_orders",
    "creates_atomicrows_bundle",
    "computes_sha_freeze_authority",
    "reduces_blockers",
    "creates_profit_evidence",
}

FALSE_SURFACE_FIELDS = {
    "accepts_external_fact",
    "binds_connector_semantics",
    "contains_computed_identity_digest",
    "contains_materialized_input_lock",
    "contains_order_receipt",
    "contains_paper_output",
    "contains_real_runtime_input",
    "contains_replay_output",
    "contains_result_packet",
    "contains_runtime_cash_receipt",
    "contains_runtime_resolver_snapshot",
    "cross_lane_write_allowed",
    "digest_computation_allowed",
    "dual_result_review_allowed",
    "dual_result_review_input_allowed",
    "input_lock_materialization_allowed",
    "input_lock_mutation_allowed",
    "lane_execution_allowed",
    "live_eligibility_creation_allowed",
    "live_eligibility_input_allowed",
    "paper_lane_may_modify_shared_inputs",
    "replay_lane_may_modify_shared_inputs",
    "result_materialization_allowed",
    "result_merge_allowed",
    "result_packet_creation_allowed",
    "runtime_resolver_snapshot_creation_allowed",
    "writes_other_lane_output_allowed",
    "writes_shared_input_identity_allowed",
}

REQUIRED_SURFACE_DEFS = {
    "execution_graph_authority_scope_flags": set(
        EXECUTION_GRAPH_AUTHORITY_SCOPE_FLAG_EXPECTATIONS
    ),
    "execution_graph_forbidden_action_flags": EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS,
    "no_claim_flags": NO_CLAIM_AUTHORITY_FIELDS,
    "shared_input_identity_placeholder": {
        "input_identity_type",
        "input_identity_id",
        "identity_state",
        "identity_material_state",
        "replay_paper_input_identity_digest_state",
        "replay_paper_input_identity_digest_reference",
        "runtime_resolver_snapshot_reference",
        "source_reference",
        "digest_computation_allowed",
        "contains_runtime_resolver_snapshot",
        "contains_real_runtime_input",
        "contains_computed_identity_digest",
        "accepts_external_fact",
        "binds_connector_semantics",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "no_claim_flags",
    },
    "immutable_input_lock_contract_placeholder": {
        "input_lock_type",
        "input_lock_id",
        "input_lock_state",
        "input_lock_digest_reference",
        "lock_required_before_lane_execution",
        "shared_input_identity_required",
        "runtime_resolver_snapshot_required",
        "input_lock_materialization_allowed",
        "input_lock_mutation_allowed",
        "replay_lane_may_modify_shared_inputs",
        "paper_lane_may_modify_shared_inputs",
        "runtime_resolver_snapshot_creation_allowed",
        "contains_materialized_input_lock",
        "contains_runtime_resolver_snapshot",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "no_claim_flags",
    },
    "lane_placeholder": {
        "lane_id",
        "lane_kind",
        "lane_state",
        "lane_execution_allowed",
        "result_packet_creation_allowed",
        "reads_shared_input_identity_required",
        "reads_immutable_input_lock_required",
        "writes_shared_input_identity_allowed",
        "writes_other_lane_output_allowed",
        "lane_output_state",
        "result_packet_boundary_reference",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "no_claim_flags",
    },
    "lane_separation_placeholder": {
        "lane_separation_type",
        "lane_separation_id",
        "lane_separation_state",
        "shared_input_identity_reference",
        "immutable_input_lock_reference",
        "lane_count_contract",
        "cross_lane_write_allowed",
        "result_merge_allowed",
        "dual_result_review_allowed",
        "live_eligibility_creation_allowed",
        "lane_placeholders",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "no_claim_flags",
    },
    "result_packet_boundary_placeholder": {
        "boundary_type",
        "boundary_id",
        "boundary_state",
        "source_reference",
        "result_packet_reference",
        "result_packet_creation_allowed",
        "result_materialization_allowed",
        "contains_result_packet",
        "contains_replay_output",
        "contains_paper_output",
        "contains_runtime_cash_receipt",
        "contains_order_receipt",
        "dual_result_review_input_allowed",
        "live_eligibility_input_allowed",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "no_claim_flags",
    },
    "replay_paper_execution_graph": {
        "graph_type",
        "graph_id",
        "graph_authority_class",
        "mode",
        "execution",
        "scaffold_state",
        "graph_state",
        "deterministic_output",
        "execution_graph_authority_scope_flags",
        "execution_graph_forbidden_action_flags",
        "shared_input_identity",
        "immutable_input_lock_contract",
        "lane_separation",
        "result_packet_boundaries",
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
    "replay_paper_execution_graph",
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
        set(EXECUTION_GRAPH_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
        label,
    )
    for field, expected in sorted(
        EXECUTION_GRAPH_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
    ):
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
        EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_AUTHORITY_FIELDS
        | FIXTURE_NO_CLAIM_FIELDS
        | FALSE_SURFACE_FIELDS
        | {
            "accepted_source_evidence_present",
            "runtime_resolver_snapshot_present",
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
        "replay_paper_execution_graph",
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
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_REPLAY_PAPER_EXECUTION_AUTHORITY"
    ):
        failures.append("schema root authority class must be static non-execution")
    if _const_value(schema, "surface_kind") != (
        "REPLAY_PAPER_EXECUTION_GRAPH_STATIC_SCAFFOLD"
    ):
        failures.append("schema root surface kind must be replay/paper graph scaffold")

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

    action_def = defs.get("execution_graph_forbidden_action_flags")
    if isinstance(action_def, dict):
        for field in sorted(EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS):
            if _const_value(action_def, field) is not False:
                failures.append(f"execution graph forbidden flag {field} must be const false")

    scope_def = defs.get("execution_graph_authority_scope_flags")
    if isinstance(scope_def, dict):
        for field, expected in sorted(
            EXECUTION_GRAPH_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
        ):
            if _const_value(scope_def, field) is not expected:
                failures.append(
                    f"execution graph authority/scope flag {field} must be const {expected}"
                )

    return failures


def _validate_scope_and_action_maps(owner: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    scope_flags, scope_failures = _mapping_at(
        owner, "execution_graph_authority_scope_flags", label
    )
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_authority_scope_flag_map(
                scope_flags, f"{label}.execution_graph_authority_scope_flags"
            )
        )

    action_flags, action_failures = _mapping_at(
        owner, "execution_graph_forbidden_action_flags", label
    )
    failures.extend(action_failures)
    if action_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                action_flags,
                EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS,
                f"{label}.execution_graph_forbidden_action_flags",
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


def _validate_shared_input_identity(identity: dict[str, Any], label: str) -> list[str]:
    failures = _require_mapping_fields(
        identity, REQUIRED_SURFACE_DEFS["shared_input_identity_placeholder"], label
    )
    failures.extend(_validate_scope_and_action_maps(identity, label))
    if identity.get("input_identity_type") != "REPLAY_PAPER_SHARED_INPUT_IDENTITY_PLACEHOLDER":
        failures.append(f"{label}.input_identity_type must be the placeholder type")
    if identity.get("identity_state") != "SCAFFOLD_ONLY_NOT_RUNTIME_IDENTITY":
        failures.append(f"{label}.identity_state must be scaffold-only")
    if identity.get("replay_paper_input_identity_digest_state") != (
        "PLACEHOLDER_ONLY_NOT_COMPUTED"
    ):
        failures.append(f"{label}.replay_paper_input_identity_digest_state must not be computed")
    return failures


def _validate_input_lock_contract(lock: dict[str, Any], label: str) -> list[str]:
    failures = _require_mapping_fields(
        lock, REQUIRED_SURFACE_DEFS["immutable_input_lock_contract_placeholder"], label
    )
    failures.extend(_validate_scope_and_action_maps(lock, label))
    if lock.get("input_lock_type") != "REPLAY_PAPER_IMMUTABLE_INPUT_LOCK_CONTRACT_PLACEHOLDER":
        failures.append(f"{label}.input_lock_type must be the placeholder type")
    if lock.get("input_lock_state") != "SCAFFOLD_ONLY_NOT_LOCKED":
        failures.append(f"{label}.input_lock_state must remain not locked")
    for required_true_field in {
        "lock_required_before_lane_execution",
        "shared_input_identity_required",
        "runtime_resolver_snapshot_required",
    }:
        if lock.get(required_true_field) is not True:
            failures.append(f"{label}.{required_true_field} must be true")
    return failures


def _validate_lanes(lane_separation: dict[str, Any], label: str) -> list[str]:
    failures = _require_mapping_fields(
        lane_separation, REQUIRED_SURFACE_DEFS["lane_separation_placeholder"], label
    )
    failures.extend(_validate_scope_and_action_maps(lane_separation, label))
    if lane_separation.get("lane_separation_state") != (
        "SCAFFOLD_ONLY_SEPARATED_NON_EXECUTING"
    ):
        failures.append(f"{label}.lane_separation_state must be separated and non-executing")
    lanes, lane_failures = _list_at(lane_separation, "lane_placeholders", label)
    failures.extend(lane_failures)
    if lanes is None:
        return failures
    if len(lanes) != 2:
        failures.append(f"{label}.lane_placeholders must contain replay and paper only")

    expected = {
        "REPLAY_LANE": ("REPLAY", "NO_REPLAY_RESULT_PACKET"),
        "PAPER_LANE": ("PAPER", "NO_PAPER_RESULT_PACKET"),
    }
    seen_lane_ids: set[str] = set()
    for index, lane in enumerate(lanes):
        lane_label = f"{label}.lane_placeholders[{index}]"
        if not isinstance(lane, dict):
            failures.append(f"{lane_label} must be an object")
            continue
        failures.extend(
            _require_mapping_fields(lane, REQUIRED_SURFACE_DEFS["lane_placeholder"], lane_label)
        )
        failures.extend(_validate_scope_and_action_maps(lane, lane_label))
        lane_id = lane.get("lane_id")
        if lane_id not in expected:
            failures.append(f"{lane_label}.lane_id must be REPLAY_LANE or PAPER_LANE")
            continue
        if lane_id in seen_lane_ids:
            failures.append(f"{lane_label}.lane_id must be unique")
        seen_lane_ids.add(lane_id)
        expected_kind, expected_output = expected[lane_id]
        if lane.get("lane_kind") != expected_kind:
            failures.append(f"{lane_label}.lane_kind must be {expected_kind}")
        if lane.get("lane_state") != "SCAFFOLD_ONLY_NOT_EXECUTED":
            failures.append(f"{lane_label}.lane_state must remain not executed")
        if lane.get("lane_output_state") != expected_output:
            failures.append(f"{lane_label}.lane_output_state must be {expected_output}")
    if seen_lane_ids != set(expected):
        failures.append(f"{label}.lane_placeholders must include separate replay and paper lanes")
    return failures


def _validate_result_boundaries(
    boundaries: list[Any], label: str
) -> list[str]:
    failures: list[str] = []
    if len(boundaries) != 2:
        failures.append(f"{label} must contain replay and paper boundaries only")

    expected_types = {
        "REPLAY_RESULT_PACKET_BOUNDARY_PLACEHOLDER",
        "PAPER_RESULT_PACKET_BOUNDARY_PLACEHOLDER",
    }
    seen_types: set[str] = set()
    for index, boundary in enumerate(boundaries):
        boundary_label = f"{label}[{index}]"
        if not isinstance(boundary, dict):
            failures.append(f"{boundary_label} must be an object")
            continue
        failures.extend(
            _require_mapping_fields(
                boundary,
                REQUIRED_SURFACE_DEFS["result_packet_boundary_placeholder"],
                boundary_label,
            )
        )
        failures.extend(_validate_scope_and_action_maps(boundary, boundary_label))
        boundary_type = boundary.get("boundary_type")
        if boundary_type not in expected_types:
            failures.append(
                f"{boundary_label}.boundary_type must be replay or paper result boundary"
            )
            continue
        if boundary_type in seen_types:
            failures.append(f"{boundary_label}.boundary_type must be unique")
        seen_types.add(boundary_type)
        if boundary.get("boundary_state") != "FUTURE_BOUNDARY_ONLY_NO_RESULT_PACKET":
            failures.append(f"{boundary_label}.boundary_state must remain future-only")
    if seen_types != expected_types:
        failures.append(f"{label} must include separate replay and paper result boundaries")
    return failures


def validate_replay_paper_execution_graph_fixture(
    fixture: dict[str, Any]
) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _require_mapping_fields(
            fixture,
            FIXTURE_REQUIRED_ROOT_FIELDS,
            "replay/paper execution graph fixture",
        )
    )

    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_REPLAY_PAPER_EXECUTION_NOT_SOURCE_FACT"
    ):
        failures.append("replay/paper execution graph fixture must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
    ):
        failures.append("replay/paper execution graph fixture example authority must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("replay/paper execution graph fixture mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("replay/paper execution graph fixture execution must be DISABLED")
    if fixture.get("schema_authority_class") != (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_REPLAY_PAPER_EXECUTION_AUTHORITY"
    ):
        failures.append("replay/paper execution graph fixture schema authority must be static-only")
    if fixture.get("surface_kind") != "REPLAY_PAPER_EXECUTION_GRAPH_STATIC_SCAFFOLD":
        failures.append("replay/paper execution graph fixture surface kind must be graph scaffold")
    if fixture.get("deterministic_output") is not True:
        failures.append("replay/paper execution graph fixture deterministic_output must be true")

    fixture_no_claim_flags, fixture_flag_failures = _mapping_at(
        fixture, "fixture_no_claim_flags", "replay/paper execution graph fixture"
    )
    failures.extend(fixture_flag_failures)
    if fixture_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                fixture_no_claim_flags,
                FIXTURE_NO_CLAIM_FIELDS,
                "replay/paper execution graph fixture.fixture_no_claim_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(
        fixture, "no_claim_flags", "replay/paper execution graph fixture"
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                NO_CLAIM_AUTHORITY_FIELDS,
                "replay/paper execution graph fixture.no_claim_flags",
            )
        )

    graph, graph_failures = _mapping_at(
        fixture,
        "replay_paper_execution_graph",
        "replay/paper execution graph fixture",
    )
    failures.extend(graph_failures)
    if graph is None:
        return failures

    graph_label = "replay_paper_execution_graph"
    failures.extend(
        _require_mapping_fields(
            graph,
            REQUIRED_SURFACE_DEFS["replay_paper_execution_graph"],
            graph_label,
        )
    )
    failures.extend(_validate_scope_and_action_maps(graph, graph_label))
    if graph.get("graph_type") != "REPLAY_PAPER_EXECUTION_GRAPH_STATIC_SCAFFOLD":
        failures.append("replay_paper_execution_graph.graph_type must be static scaffold")
    if graph.get("graph_authority_class") != (
        "STATIC_REPLAY_PAPER_EXECUTION_GRAPH_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append("replay_paper_execution_graph authority class must be static-only")
    if graph.get("mode") != "SOURCE_REQUIRED":
        failures.append("replay_paper_execution_graph mode must be SOURCE_REQUIRED")
    if graph.get("execution") != "DISABLED":
        failures.append("replay_paper_execution_graph execution must be DISABLED")
    if graph.get("scaffold_state") != "SCAFFOLD_ONLY":
        failures.append("replay_paper_execution_graph scaffold_state must be SCAFFOLD_ONLY")
    if graph.get("graph_state") != "SCAFFOLD_ONLY_NOT_EXECUTABLE":
        failures.append("replay_paper_execution_graph graph_state must remain not executable")

    shared_identity, shared_failures = _mapping_at(
        graph, "shared_input_identity", graph_label
    )
    failures.extend(shared_failures)
    if shared_identity is not None:
        failures.extend(
            _validate_shared_input_identity(
                shared_identity, f"{graph_label}.shared_input_identity"
            )
        )

    input_lock, lock_failures = _mapping_at(
        graph, "immutable_input_lock_contract", graph_label
    )
    failures.extend(lock_failures)
    if input_lock is not None:
        failures.extend(
            _validate_input_lock_contract(
                input_lock, f"{graph_label}.immutable_input_lock_contract"
            )
        )

    lane_separation, lane_separation_failures = _mapping_at(
        graph, "lane_separation", graph_label
    )
    failures.extend(lane_separation_failures)
    if lane_separation is not None:
        failures.extend(
            _validate_lanes(lane_separation, f"{graph_label}.lane_separation")
        )

    boundaries, boundary_failures = _list_at(
        graph, "result_packet_boundaries", graph_label
    )
    failures.extend(boundary_failures)
    if boundaries is not None:
        failures.extend(
            _validate_result_boundaries(
                boundaries, f"{graph_label}.result_packet_boundaries"
            )
        )

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
        failures.extend(validate_replay_paper_execution_graph_fixture(fixture))

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
            "REPLAY_PAPER_EXECUTION_GRAPH_STATIC_VALIDATION_FAILED\n- "
            + "\n- ".join(failures)
        )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
