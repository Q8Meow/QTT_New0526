#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

SUCCESS_MARKER = "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_VALIDATION_OK"
FAILURE_MARKER = "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_VALIDATION_FAILED"

SCHEMA_AUTHORITY_CLASS = "STATIC_STAGE1_RUNTIME_SCAFFOLD_GATE_CONTRACT_ONLY"
SURFACE_KIND = "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC"
SURFACE_VERSION = "PR36_STAGE1_RUNTIME_SCAFFOLD_GATE_SCHEMA_V1"
VALIDATION_HOOK = "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_AUDIT"

SOURCE_REQUIRED = "SOURCE_REQUIRED"
RUNTIME_OBSERVATION_REQUIRED = "RUNTIME_OBSERVATION_REQUIRED"
UNBOUND = "UNBOUND"

CANONICAL_BUNDLE_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

EXPECTED_SCAFFOLD_AREAS = [
    "resolver_scaffold",
    "resolver_input_lock_scaffold",
    "replay_paper_shared_input_lock_scaffold",
    "replay_lane_scaffold",
    "paper_lane_scaffold",
    "dual_result_review_scaffold",
    "arbitrage_comparability_scaffold",
    "dashboard_duration_owner_control_scaffold",
    "capital_cash_component_receipt_scaffold",
    "pretrade_gate_snapshot_scaffold",
    "transition_runtime_state_machine_scaffold",
    "stage1_runtime_scaffold_gate_report",
]

EXPECTED_AREA_PLACEHOLDERS = {
    "resolver_scaffold": [
        "SNAPSHOT_PACKET_BUILDER_METHOD_SIGNATURE_PLACEHOLDER",
        "SOURCE_REQUIRED_ROUTE_PLACEHOLDER",
        "RUNTIME_OBSERVATION_REQUIRED_ROUTE_PLACEHOLDER",
    ],
    "resolver_input_lock_scaffold": [
        "RESOLVER_INPUT_LOCK_CONTRACT_PLACEHOLDER",
        "IMMUTABLE_INPUT_REFERENCE_PLACEHOLDER",
    ],
    "replay_paper_shared_input_lock_scaffold": [
        "SHARED_IMMUTABLE_INPUT_LOCK_CONTRACT_PLACEHOLDER",
        "SEPARATE_LANE_INPUT_REFERENCE_PLACEHOLDER",
    ],
    "replay_lane_scaffold": [
        "REPLAY_LANE_CONTRACT_PLACEHOLDER",
        "REPLAY_EXECUTION_DISABLED_RECEIPT_PLACEHOLDER",
    ],
    "paper_lane_scaffold": [
        "PAPER_LANE_CONTRACT_PLACEHOLDER",
        "PAPER_EXECUTION_DISABLED_RECEIPT_PLACEHOLDER",
    ],
    "dual_result_review_scaffold": [
        "DUAL_RESULT_REVIEW_CONTRACT_PLACEHOLDER",
        "NO_DECISION_RECEIPT_PLACEHOLDER",
    ],
    "arbitrage_comparability_scaffold": [
        "COMPARABILITY_CONTRACT_PLACEHOLDER",
        "CROSS_VENUE_WRITE_BLOCKED_PLACEHOLDER",
    ],
    "dashboard_duration_owner_control_scaffold": [
        "DURATION_CHANGE_CONTRACT_PLACEHOLDER",
        "OWNER_CONTROL_CONTRACT_PLACEHOLDER",
    ],
    "capital_cash_component_receipt_scaffold": [
        "CASH_COMPONENT_RECEIPT_CONTRACT_PLACEHOLDER",
        "NO_RUNTIME_CASH_CLAIM_PLACEHOLDER",
    ],
    "pretrade_gate_snapshot_scaffold": [
        "PRETRADE_GATE_SNAPSHOT_CONTRACT_PLACEHOLDER",
        "NO_INCREASED_EXPOSURE_PLACEHOLDER",
    ],
    "transition_runtime_state_machine_scaffold": [
        "STATE_MACHINE_CONTRACT_PLACEHOLDER",
        "FAIL_CLOSED_GATE_PLACEHOLDER",
    ],
    "stage1_runtime_scaffold_gate_report": [
        "STATIC_GATE_REPORT_CONTRACT_PLACEHOLDER",
        "NON_MUTATING_VALIDATION_RECEIPT_PLACEHOLDER",
    ],
}

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
    "expected_scaffold_areas",
    "scaffold_area_contracts",
    "resolver_policy",
    "input_lock_policy",
    "replay_paper_policy",
    "arbitrage_policy",
    "dashboard_policy",
    "capital_risk_policy",
    "transition_runtime_policy",
    "source_authority_policy",
    "connector_semantic_policy",
    "network_policy",
    "live_reachability_policy",
    "order_authority_policy",
    "atomicrows_authority_state",
    "claim_policy",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR36_STAGE1_RUNTIME_SCAFFOLD_GATE_BLOCKED_FIXTURE",
    "fixture_version": "PR36_STAGE1_RUNTIME_SCAFFOLD_GATE_BLOCKED_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_STAGE1_RUNTIME_AUTHORITY"
    ),
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "surface_kind": SURFACE_KIND,
    "surface_version": SURFACE_VERSION,
    "mode": SOURCE_REQUIRED,
    "execution": "DISABLED",
    "validation_mode": "STATIC_SCHEMA_ONLY_NON_MUTATING_AUDIT",
    "deterministic_output": True,
}

GATE_AUTHORITY_EXPECTATIONS = {
    "static_audit_only": True,
    "schema_only": True,
    "scaffold_only": True,
    "non_mutating_validator": True,
    "runtime_authority_created": False,
    "runtime_execution_created": False,
    "source_authority_created": False,
    "connector_binding_authority_created": False,
    "live_reachability_authority_created": False,
    "order_authority_created": False,
    "atomicrows_authority_created": False,
    "blocker_reduction_authority_created": False,
    "profit_authority_created": False,
}

PREREQUISITE_RECEIPT_EXPECTATIONS = {
    "connector_scaffold_source_required_gate_receipt_required": True,
    "connector_scaffold_source_required_gate_receipt_status": "REQUIRED",
    "venue_neutral_prediction_adapter_gate_receipt_required": True,
    "venue_neutral_prediction_adapter_gate_receipt_status": "REQUIRED",
    "stage1_packet_schema_gate_receipt_required": True,
    "stage1_packet_schema_gate_receipt_status": "REQUIRED",
    "source_evidence_gate_confirmation_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_status": "REQUIRED",
    "prerequisite_receipts_create_runtime_authority": False,
    "prerequisite_receipts_create_source_authority": False,
    "prerequisite_receipts_create_connector_binding_authority": False,
    "prerequisite_receipts_create_order_authority": False,
}

RESOLVER_POLICY_EXPECTATIONS = {
    "snapshot_packet_builder_placeholder_allowed": True,
    "runtime_resolver_snapshot_emission_allowed": False,
    "runtime_resolver_snapshot_created": False,
    "runtime_resolver_snapshot_creation_claimed": False,
    "exact_market_selection_allowed": False,
    "exact_market_selection_claimed": False,
    "exact_contract_selection_allowed": False,
    "exact_contract_selection_claimed": False,
    "exact_event_selection_allowed": False,
    "exact_event_selection_claimed": False,
    "exact_symbol_selection_allowed": False,
    "exact_symbol_selection_claimed": False,
    "exact_live_venue_selection_allowed": False,
    "exact_live_venue_selection_claimed": False,
    "missing_accepted_packet_route": SOURCE_REQUIRED,
    "missing_runtime_input_route": RUNTIME_OBSERVATION_REQUIRED,
    "source_required_route_required": True,
    "runtime_observation_required_route_required": True,
    "accepted_source_packets_required_before_resolution": True,
    "runtime_inputs_required_before_resolution": True,
}

INPUT_LOCK_POLICY_EXPECTATIONS = {
    "resolver_input_lock_contract_allowed": True,
    "shared_replay_paper_input_lock_contract_allowed": True,
    "immutable_input_lock_placeholder_allowed": True,
    "runtime_input_lock_creation_allowed": False,
    "runtime_input_lock_created": False,
    "runtime_input_mutation_allowed": False,
    "replay_paper_shared_input_lock_only": True,
    "separate_replay_and_paper_lanes_required": True,
}

REPLAY_PAPER_POLICY_EXPECTATIONS = {
    "shared_immutable_input_lock_defined": True,
    "separate_replay_lane_defined": True,
    "separate_paper_lane_defined": True,
    "replay_execution_allowed": False,
    "replay_execution_claimed": False,
    "paper_execution_allowed": False,
    "paper_execution_claimed": False,
    "runtime_replay_result_packet_creation_allowed": False,
    "runtime_replay_result_packet_created": False,
    "runtime_paper_result_packet_creation_allowed": False,
    "runtime_paper_result_packet_created": False,
    "replay_paper_result_creation_allowed": False,
    "replay_paper_merge_allowed": False,
    "replay_paper_merge_claimed": False,
    "dual_result_review_contract_allowed": True,
    "dual_result_review_decision_allowed": False,
    "dual_result_review_decision_created": False,
    "dual_result_review_merge_allowed": False,
}

ARBITRAGE_POLICY_EXPECTATIONS = {
    "comparability_contracts_allowed": True,
    "comparability_placeholders_only": True,
    "exact_contract_event_match_claim_allowed": False,
    "exact_contract_event_match_claimed": False,
    "live_arbitrage_enabled": False,
    "live_arbitrage_enablement_claimed": False,
    "cross_venue_order_routing_allowed": False,
    "cross_venue_order_write_allowed": False,
    "cross_venue_order_write_permission_claimed": False,
}

DASHBOARD_POLICY_EXPECTATIONS = {
    "duration_change_contract_allowed": True,
    "owner_control_contract_allowed": True,
    "active_run_mutation_allowed": False,
    "active_run_mutation_claimed": False,
    "dashboard_runtime_state_mutation_allowed": False,
    "live_effective_value_mutation_allowed": False,
    "live_effective_value_mutation_claimed": False,
    "observed_fact_rewrite_allowed": False,
    "observed_fact_rewrite_claimed": False,
    "source_fact_rewrite_allowed": False,
    "source_fact_rewrite_claimed": False,
    "market_data_rewrite_allowed": False,
    "market_data_rewrite_claimed": False,
    "replay_result_fact_rewrite_allowed": False,
    "replay_result_fact_rewrite_claimed": False,
    "paper_result_fact_rewrite_allowed": False,
    "paper_result_fact_rewrite_claimed": False,
    "runtime_balance_rewrite_allowed": False,
    "runtime_balance_rewrite_claimed": False,
}

CAPITAL_RISK_POLICY_EXPECTATIONS = {
    "cash_component_receipt_contract_allowed": True,
    "pretrade_gate_snapshot_contract_allowed": True,
    "runtime_cash_claim_allowed": False,
    "runtime_cash_claimed": False,
    "usable_cash_claim_allowed": False,
    "usable_cash_claimed": False,
    "increased_exposure_allowed": False,
    "increased_exposure_claimed": False,
    "runtime_balance_claim_allowed": False,
    "runtime_balance_claimed": False,
    "private_state_fetch_allowed": False,
    "balance_fetch_allowed": False,
    "account_state_fetch_allowed": False,
    "positions_fetch_allowed": False,
    "orders_fetch_allowed": False,
}

TRANSITION_RUNTIME_POLICY_EXPECTATIONS = {
    "state_machine_placeholder_allowed": True,
    "fail_closed_gate_placeholder_allowed": True,
    "limited_live_canary_promotion_allowed": False,
    "limited_live_canary_promotion_claimed": False,
    "triggered_live_comparison_promotion_allowed": False,
    "triggered_live_comparison_promotion_claimed": False,
    "full_live_promotion_allowed": False,
    "full_live_promotion_claimed": False,
    "scaled_live_promotion_allowed": False,
    "scaled_live_promotion_claimed": False,
    "limited_live_arbitrage_promotion_allowed": False,
    "limited_live_arbitrage_promotion_claimed": False,
    "live_transition_execution_allowed": False,
}

SOURCE_AUTHORITY_POLICY_EXPECTATIONS = {
    "source_retrieval_claimed": False,
    "source_acceptance_claimed": False,
    "source_facts_accepted": False,
    "accepted_source_packet_created": False,
    "accepted_source_evidence_packet_created": False,
    "accepted_source_packets_present": False,
    "accepted_source_packet_reference": UNBOUND,
    "accepted_source_evidence_packet_reference": UNBOUND,
}

CONNECTOR_SEMANTIC_POLICY_EXPECTATIONS = {
    "connector_semantic_binding_allowed": False,
    "connector_semantic_binding_claimed": False,
    "connector_semantics_bound": False,
    "connector_semantic_values_population_allowed": False,
    "connector_semantic_values_populated": False,
    "connector_semantic_value_reference": SOURCE_REQUIRED,
    "connector_semantic_value_route": SOURCE_REQUIRED,
}

NETWORK_POLICY_EXPECTATIONS = {
    "network_io_created": False,
    "network_io_allowed": False,
    "http_client_created": False,
    "websocket_client_created": False,
    "live_connector_client_created": False,
    "live_connector_client_creation_allowed": False,
    "venue_api_call_allowed": False,
    "live_connector_reference": UNBOUND,
}

LIVE_REACHABILITY_POLICY_EXPECTATIONS = {
    "live_reachability_allowed": False,
    "live_reachability_created": False,
    "live_reachability_claimed": False,
}

ORDER_AUTHORITY_POLICY_EXPECTATIONS = {
    "order_authority_created": False,
    "order_execution_authority_created": False,
    "order_authority_claimed": False,
    "cross_venue_order_write_allowed": False,
    "order_submission_enabled": False,
    "order_cancel_enabled": False,
    "order_reduce_enabled": False,
    "order_close_enabled": False,
}

ATOMICROWS_STATE_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": False,
    "canonical_bundle_sha_present": False,
    "atomicrows_bundle_creation_claimed": False,
    "atomicrows_hash_creation_claimed": False,
    "atomicrows_sha_computation_claimed": False,
    "atomicrows_sha_authority_claimed": False,
    "atomicrows_row_creation_claimed": False,
    "atomicrows_completion_claimed": False,
    "claims_4183_row_completion": False,
    "freeze_authority_claimed": False,
}

CLAIM_POLICY_EXPECTATIONS = {
    "blocker_reduction_allowed": False,
    "blocker_reduction_claimed": False,
    "profit_claim_allowed": False,
    "profit_claim_created": False,
    "profit_evidence_allowed": False,
    "profit_evidence_created": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "source_fact_acceptance_enabled",
    "accepted_source_packet_creation_enabled",
    "accepted_source_evidence_packet_creation_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "connector_semantic_value_population_enabled",
    "network_io_enabled",
    "http_client_enabled",
    "websocket_client_enabled",
    "live_connector_client_creation_enabled",
    "venue_api_call_enabled",
    "exact_market_selection_enabled",
    "exact_contract_selection_enabled",
    "exact_event_selection_enabled",
    "exact_symbol_selection_enabled",
    "exact_live_venue_selection_enabled",
    "runtime_resolver_snapshot_emission_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "runtime_input_lock_creation_enabled",
    "runtime_input_mutation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "runtime_replay_result_packet_creation_enabled",
    "runtime_paper_result_packet_creation_enabled",
    "replay_paper_result_creation_enabled",
    "replay_paper_merge_enabled",
    "dual_result_review_decision_enabled",
    "dual_result_review_merge_enabled",
    "live_arbitrage_enabled",
    "cross_venue_order_routing_enabled",
    "cross_venue_order_write_enabled",
    "dashboard_active_run_mutation_enabled",
    "dashboard_runtime_state_mutation_enabled",
    "live_effective_value_mutation_enabled",
    "observed_fact_rewrite_enabled",
    "source_fact_rewrite_enabled",
    "market_data_rewrite_enabled",
    "replay_result_fact_rewrite_enabled",
    "paper_result_fact_rewrite_enabled",
    "runtime_balance_rewrite_enabled",
    "runtime_cash_claim_enabled",
    "usable_cash_claim_enabled",
    "increased_exposure_enabled",
    "runtime_balance_claim_enabled",
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "account_state_fetch_enabled",
    "positions_fetch_enabled",
    "orders_fetch_enabled",
    "limited_live_canary_promotion_enabled",
    "triggered_live_comparison_promotion_enabled",
    "full_live_promotion_enabled",
    "scaled_live_promotion_enabled",
    "limited_live_arbitrage_promotion_enabled",
    "live_transition_execution_enabled",
    "live_reachability_enabled",
    "order_authority_enabled",
    "order_execution_authority_enabled",
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
    "creates_network_io",
    "creates_live_connector_client",
    "selects_exact_markets",
    "selects_exact_contracts",
    "selects_exact_events",
    "selects_exact_symbols",
    "selects_live_venues",
    "emits_runtime_resolver_snapshots",
    "creates_runtime_resolver_snapshots",
    "creates_runtime_input_locks",
    "mutates_runtime_inputs",
    "executes_replay",
    "executes_paper",
    "creates_runtime_replay_result_packets",
    "creates_runtime_paper_result_packets",
    "creates_replay_paper_results",
    "merges_replay_and_paper_results",
    "creates_dual_result_review_decisions",
    "enables_live_arbitrage",
    "permits_cross_venue_order_routing",
    "permits_cross_venue_order_writes",
    "mutates_dashboard_active_runs",
    "mutates_dashboard_runtime_state",
    "mutates_live_effective_values",
    "rewrites_observed_facts",
    "rewrites_source_facts",
    "rewrites_market_data",
    "rewrites_replay_result_facts",
    "rewrites_paper_result_facts",
    "rewrites_runtime_balances",
    "claims_runtime_cash",
    "claims_usable_cash",
    "claims_increased_exposure",
    "fetches_private_state",
    "fetches_balances",
    "fetches_account_state",
    "fetches_positions",
    "fetches_orders",
    "promotes_limited_live_canary",
    "promotes_triggered_live_comparison",
    "promotes_full_live",
    "promotes_scaled_live",
    "promotes_limited_live_arbitrage",
    "creates_live_reachability",
    "creates_order_authority",
    "creates_order_execution_authority",
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

SCAFFOLD_CONTRACT_FIELDS = {
    "area_id",
    "scaffold_kind",
    "scaffold_state",
    "contract_scope",
    "contract_only",
    "schema_placeholder_only",
    "allowed_contract_placeholders",
    "source_required_route",
    "runtime_observation_required_route",
    "runtime_authority_created",
    "runtime_execution_allowed",
    "live_authority_created",
    "order_authority_created",
    "source_authority_created",
    "connector_binding_authority_created",
    "blocker_reduction_claimed",
    "profit_claim_created",
}

SCAFFOLD_CONTRACT_EXPECTATIONS = {
    "scaffold_state": "SCAFFOLD_ONLY_NOT_RUNTIME",
    "contract_scope": "STATIC_CONTRACT_PLACEHOLDER_ONLY",
    "contract_only": True,
    "schema_placeholder_only": True,
    "source_required_route": SOURCE_REQUIRED,
    "runtime_observation_required_route": RUNTIME_OBSERVATION_REQUIRED,
    "runtime_authority_created": False,
    "runtime_execution_allowed": False,
    "live_authority_created": False,
    "order_authority_created": False,
    "source_authority_created": False,
    "connector_binding_authority_created": False,
    "blocker_reduction_claimed": False,
    "profit_claim_created": False,
}

EXPECTED_MAP_DEFS = {
    "gate_authority": GATE_AUTHORITY_EXPECTATIONS,
    "prerequisite_receipts": PREREQUISITE_RECEIPT_EXPECTATIONS,
    "resolver_policy": RESOLVER_POLICY_EXPECTATIONS,
    "input_lock_policy": INPUT_LOCK_POLICY_EXPECTATIONS,
    "replay_paper_policy": REPLAY_PAPER_POLICY_EXPECTATIONS,
    "arbitrage_policy": ARBITRAGE_POLICY_EXPECTATIONS,
    "dashboard_policy": DASHBOARD_POLICY_EXPECTATIONS,
    "capital_risk_policy": CAPITAL_RISK_POLICY_EXPECTATIONS,
    "transition_runtime_policy": TRANSITION_RUNTIME_POLICY_EXPECTATIONS,
    "source_authority_policy": SOURCE_AUTHORITY_POLICY_EXPECTATIONS,
    "connector_semantic_policy": CONNECTOR_SEMANTIC_POLICY_EXPECTATIONS,
    "network_policy": NETWORK_POLICY_EXPECTATIONS,
    "live_reachability_policy": LIVE_REACHABILITY_POLICY_EXPECTATIONS,
    "order_authority_policy": ORDER_AUTHORITY_POLICY_EXPECTATIONS,
    "atomicrows_authority_state": ATOMICROWS_STATE_EXPECTATIONS,
    "claim_policy": CLAIM_POLICY_EXPECTATIONS,
    "forbidden_action_flags": {field: False for field in FORBIDDEN_ACTION_FLAGS},
    "no_claim_flags": {field: False for field in NO_CLAIM_FLAGS},
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
    "requests.",
    "aiohttp",
    "httpx",
    "urllib",
    "websockets.",
    "websocketclient",
    "venue_sdk",
    "runtimeclient",
    "exact_contract:",
    "exact_event:",
    "exact_market:",
    "live_venue:",
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


def _actual_atomicrows_presence(repo_root: pathlib.Path) -> tuple[bool, bool]:
    root = repo_root.resolve()
    bundle_path = _canonical_path(root, CANONICAL_BUNDLE_RELATIVE_PATH)
    sha_path = _canonical_path(root, CANONICAL_BUNDLE_SHA_RELATIVE_PATH)
    return bundle_path.exists(), sha_path.exists()


def _validate_schema_map_definition(
    definition: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> list[str]:
    failures: list[str] = []
    if definition.get("type") != "object":
        failures.append(f"{label}.type must be object")
    if definition.get("additionalProperties") is not False:
        failures.append(f"{label}.additionalProperties must be false")
    properties = _properties(definition)
    required = _required(definition)
    failures.extend(_require_exact_fields(properties, set(expected), f"{label}.properties"))
    if required != set(expected):
        missing = sorted(set(expected) - required)
        unexpected = sorted(required - set(expected))
        if missing:
            failures.append(f"{label} missing required fields: {', '.join(missing)}")
        if unexpected:
            failures.append(f"{label} has unexpected required fields: {', '.join(unexpected)}")
    for field, expected_value in sorted(expected.items()):
        if _const_value(definition, field) != expected_value:
            failures.append(f"{label}.{field} must be const {expected_value}")
    return failures


def _validate_scaffold_contract_schema(definition: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if definition.get("type") != "object":
        failures.append("scaffold_area_contract.type must be object")
    if definition.get("additionalProperties") is not False:
        failures.append("scaffold_area_contract.additionalProperties must be false")
    properties = _properties(definition)
    required = _required(definition)
    failures.extend(
        _require_exact_fields(
            properties,
            SCAFFOLD_CONTRACT_FIELDS,
            "scaffold_area_contract.properties",
        )
    )
    if required != SCAFFOLD_CONTRACT_FIELDS:
        missing = sorted(SCAFFOLD_CONTRACT_FIELDS - required)
        unexpected = sorted(required - SCAFFOLD_CONTRACT_FIELDS)
        if missing:
            failures.append(
                f"scaffold_area_contract missing required fields: {', '.join(missing)}"
            )
        if unexpected:
            failures.append(
                "scaffold_area_contract has unexpected required fields: "
                + ", ".join(unexpected)
            )
    return failures


def _validate_schema(schema: dict[str, Any], schema_path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected_id = (
        "https://qtt.local/schemas/runtime_orchestration/"
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
    failures.extend(_require_exact_fields(properties, ROOT_FIELDS, "schema.properties"))
    if required != ROOT_FIELDS:
        missing = sorted(ROOT_FIELDS - required)
        unexpected = sorted(required - ROOT_FIELDS)
        if missing:
            failures.append(f"schema root missing required fields: {', '.join(missing)}")
        if unexpected:
            failures.append(
                f"schema root has unexpected required fields: {', '.join(unexpected)}"
            )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"schema root {field} must be const {expected}")
    for field in sorted(EXPECTED_MAP_DEFS):
        if _ref_value(schema, field) != f"#/$defs/{field}":
            failures.append(f"schema root {field} must reference #/$defs/{field}")
    scaffold_contracts = properties.get("scaffold_area_contracts", {})
    if (
        not isinstance(scaffold_contracts, dict)
        or scaffold_contracts.get("items", {}).get("$ref")
        != "#/$defs/scaffold_area_contract"
    ):
        failures.append(
            "schema root scaffold_area_contracts must reference scaffold_area_contract"
        )
    validation_hooks = properties.get("validation_hook_ids", {})
    if (
        not isinstance(validation_hooks, dict)
        or validation_hooks.get("items", {}).get("const") != VALIDATION_HOOK
    ):
        failures.append("schema validation_hook_ids must require the Stage-1 hook")

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema missing $defs object"]
    for def_name, expectations in sorted(EXPECTED_MAP_DEFS.items()):
        definition = defs.get(def_name)
        if not isinstance(definition, dict):
            failures.append(f"schema missing required definition: {def_name}")
            continue
        failures.extend(
            _validate_schema_map_definition(
                definition,
                expectations,
                def_name,
            )
        )
    contract_definition = defs.get("scaffold_area_contract")
    if not isinstance(contract_definition, dict):
        failures.append("schema missing required definition: scaffold_area_contract")
    else:
        failures.extend(_validate_scaffold_contract_schema(contract_definition))
    return failures


def _validate_scaffold_area_contracts(records: Any) -> list[str]:
    if not isinstance(records, list) or not records:
        return ["scaffold_area_contracts must be a non-empty list"]
    failures: list[str] = []
    seen: list[str] = []
    for index, record in enumerate(records):
        label = f"scaffold_area_contracts[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(record, SCAFFOLD_CONTRACT_FIELDS, label))
        area_id = record.get("area_id")
        if isinstance(area_id, str):
            seen.append(area_id)
        if area_id not in EXPECTED_AREA_PLACEHOLDERS:
            failures.append(f"{label}.area_id must be an expected scaffold area")
            continue
        if record.get("scaffold_kind") != area_id.upper():
            failures.append(f"{label}.scaffold_kind must match upper-case area_id")
        for field, expected_value in sorted(SCAFFOLD_CONTRACT_EXPECTATIONS.items()):
            if record.get(field) != expected_value:
                failures.append(f"{label}.{field} must be {expected_value}")
        if record.get("allowed_contract_placeholders") != EXPECTED_AREA_PLACEHOLDERS[area_id]:
            failures.append(
                f"{label}.allowed_contract_placeholders must match expected placeholders"
            )
    if seen != EXPECTED_SCAFFOLD_AREAS:
        failures.append(
            "scaffold_area_contracts must preserve the expected Stage-1 scaffold area order"
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
            "canonical AtomicRows bundle must remain absent during Stage-1 runtime "
            f"scaffold gate validation: {CANONICAL_BUNDLE_RELATIVE_PATH}"
        )
    if sha_present:
        failures.append(
            "canonical AtomicRows bundle hash must remain absent during Stage-1 "
            f"runtime scaffold gate validation: {CANONICAL_BUNDLE_SHA_RELATIVE_PATH}"
        )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expectation_maps = list(EXPECTED_MAP_DEFS.values()) + [SCAFFOLD_CONTRACT_EXPECTATIONS]
    must_be_false = (
        FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_FLAGS
        | {
            field
            for expected in expectation_maps
            for field, value in expected.items()
            if value is False
        }
    )
    must_be_true = {
        field
        for expected in expectation_maps
        for field, value in expected.items()
        if value is True
    }

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain AtomicRows row records")
        if key in {"source_required_route", "missing_accepted_packet_route"} and item != (
            SOURCE_REQUIRED
        ):
            failures.append(f"{path} must route to {SOURCE_REQUIRED}")
        if key in {
            "runtime_observation_required_route",
            "missing_runtime_input_route",
        } and item != RUNTIME_OBSERVATION_REQUIRED:
            failures.append(f"{path} must route to {RUNTIME_OBSERVATION_REQUIRED}")
        if key == "connector_semantic_value_reference":
            if item != SOURCE_REQUIRED:
                failures.append(f"{path} must remain {SOURCE_REQUIRED}")
        elif key.endswith("_reference") and item != UNBOUND:
            failures.append(f"{path} must remain {UNBOUND}")
        if type(item) in {int, float}:
            failures.append(f"{path} must not contain numeric runtime or venue values")
        if isinstance(item, str):
            lowered = item.lower()
            if path.startswith("fixture.atomicrows_authority_state") and key in {
                "canonical_bundle_path",
                "canonical_bundle_sha_path",
            }:
                continue
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_stage1_runtime_scaffold_gate_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "stage1 runtime scaffold gate fixture",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(
                f"stage1 runtime scaffold gate fixture.{field} must be {expected}"
            )

    if fixture.get("expected_scaffold_areas") != EXPECTED_SCAFFOLD_AREAS:
        failures.append("expected_scaffold_areas must match required scaffold areas")
    failures.extend(_validate_scaffold_area_contracts(fixture.get("scaffold_area_contracts")))

    for field, expectations in sorted(EXPECTED_MAP_DEFS.items()):
        value, map_failures = _mapping(
            fixture,
            field,
            "stage1 runtime scaffold gate fixture",
        )
        failures.extend(map_failures)
        if value is None:
            continue
        if field == "atomicrows_authority_state":
            failures.extend(_validate_atomicrows_state(value, repo_root=repo_root))
        else:
            failures.extend(_validate_const_map(value, expectations, field))

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
        failures.extend(_validate_schema(schema, schema_path))
    if fixture is not None:
        failures.extend(
            validate_stage1_runtime_scaffold_gate_fixture(
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
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
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
