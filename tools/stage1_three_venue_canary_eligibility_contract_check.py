#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
from typing import Any, Sequence

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from qtt.core.testing.gate_result import (  # noqa: E402
    load_json_object,
    require_bool_map,
    require_exact_fields,
    true_claim_failures,
    validate_current_atomicrows_bundle_state,
    write_json,
)

SUCCESS_MARKER = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_OK"
FAILURE_MARKER = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_STATIC_AUDIT"

INPUT_CONTRACT_TYPE = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_INPUT_CONTRACT"
READINESS_MATRIX_TYPE = "STAGE1_THREE_VENUE_PLATFORM_READINESS_MATRIX"
HANDOFF_TYPE = "STAGE1_OWNER_REVIEW_TO_CANARY_ELIGIBILITY_HANDOFF"
GATE_REPORT_TYPE = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_GATE_REPORT"
EXECUTION_BLOCK_TYPE = "STAGE1_LIMITED_LIVE_CANARY_EXECUTION_BLOCK"

EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
STATIC_GATE_STATE = "STATIC_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
OWNER_REVIEW_TO_CANARY_CONSUMER = "THREE_VENUE_CANARY_ELIGIBILITY_GATE_ONLY"
LIMITED_LIVE_BOUNDARY_CONSUMER = "LIMITED_LIVE_CANARY_EXECUTION_BOUNDARY_ONLY"
PLATFORM_SCOPE_TYPE = "KALSHI_POLYMARKET_FORECASTEX_IBKR"
CANONICAL_PLATFORMS = ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]

DEFAULT_INPUT_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_three_venue_canary_eligibility_input_contract.schema.json"
)
DEFAULT_READINESS_MATRIX_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_three_venue_platform_readiness_matrix.schema.json"
)
DEFAULT_HANDOFF_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
)
DEFAULT_GATE_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_three_venue_canary_eligibility_gate_report.schema.json"
)
DEFAULT_EXECUTION_BLOCK_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_limited_live_canary_execution_block.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/three_venue_canary_eligibility/"
    "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
)
DEFAULT_MASTER_PLAN = pathlib.Path("docs/master_plan/QTT_MasterPlan_Current.md")

NO_CLAIM_FLAGS = {
    "retrieves_source_evidence": False,
    "accepts_source_facts": False,
    "creates_real_accepted_source_evidence": False,
    "creates_accepted_source_packets": False,
    "populates_production_connector_semantic_values": False,
    "imports_live_clients": False,
    "creates_network_io": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_replay_result_packets": False,
    "creates_paper_result_packets": False,
    "merges_replay_paper_results": False,
    "creates_dual_result_review_decision": False,
    "creates_owner_live_promotion_review": False,
    "creates_owner_approval_receipt": False,
    "creates_live_eligibility": False,
    "creates_three_venue_canary_eligibility": False,
    "creates_limited_live_canary_execution": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FALSE_BOUNDARY_FIELDS = {
    "accepted_source_fact_created",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "auto_canary_eligibility_claimed_flag",
    "auto_live_promotion_claimed_flag",
    "blocker_reduction_claim_allowed_flag",
    "blocker_reduction_claim_created_flag",
    "canary_execution_receipt_created_flag",
    "connector_semantics_created_flag",
    "direct_canary_execution_allowed_flag",
    "direct_canary_execution_claimed_flag",
    "direct_full_scaled_live_allowed_flag",
    "direct_live_arbitrage_allowed_flag",
    "direct_live_order_router_allowed_flag",
    "direct_limited_live_canary_execution_allowed_flag",
    "future_owner_risk_reduction_override_present_flag",
    "live_api_reachability_created_flag",
    "live_eligibility_allowed_flag",
    "limited_live_canary_execution_allowed_flag",
    "limited_live_canary_execution_allowed_flag",
    "limited_live_canary_execution_created_flag",
    "live_market_selection_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "order_placement_authority_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "partial_platform_launch_allowed_flag",
    "production_connector_semantic_values_populated_flag",
    "profit_claim_allowed_flag",
    "real_platform_readiness_created_flag",
    "runtime_cash_claim_allowed_flag",
    "runtime_cash_claim_created_flag",
    "silent_single_venue_fallback_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "three_venue_canary_eligibility_green_flag",
}

TRUE_BOUNDARY_FIELDS = {
    "all_three_platforms_required_flag",
    "matrix_entries_non_execution_flag",
    "matrix_entries_non_live_flag",
    "owner_approval_receipt_required_before_canary_eligibility_flag",
    "owner_review_required_before_canary_eligibility_flag",
    "partial_platform_launch_requires_future_owner_risk_reduction_override_flag",
    "platform_specific_readiness_placeholder_only_flag",
    "upstream_receipt_references_immutable_flag",
    "upstream_report_references_immutable_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | FALSE_BOUNDARY_FIELDS | {
    "atomicrows_bundle_created",
    "atomicrows_hash_created",
    "blocker_reduction_claimed",
    "canary_eligibility_created",
    "canary_execution_created",
    "live_order_authority_created",
    "owner_approval_receipt_created",
    "owner_live_promotion_approval_created",
    "profit_evidence_created",
    "runtime_cash_receipt_created",
}

FORBIDDEN_COUNT_FIELDS = {
    "accepted_source_fact_created_count",
    "atomicrows_bundle_hash_mutation_claim_count",
    "blocker_reduction_claim_count",
    "canary_execution_claim_count",
    "live_order_runtime_cash_profit_claim_count",
    "owner_approval_receipt_created_count",
}

INPUT_CONTRACT_FIELDS = {
    "three_venue_canary_eligibility_input_contract_type",
    "three_venue_canary_eligibility_input_contract_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "owner_live_promotion_review_gate_report_ref",
    "owner_live_promotion_review_gate_report_digest",
    "owner_live_promotion_review_gate_report_state",
    "owner_review_freshness_state",
    "owner_approval_receipt_boundary_ref",
    "owner_approval_receipt_boundary_digest",
    "owner_approval_receipt_boundary_state",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "owner_approval_receipt_required_before_canary_eligibility_flag",
    "owner_review_required_before_canary_eligibility_flag",
    "upstream_report_references_immutable_flag",
    "upstream_receipt_references_immutable_flag",
    "platform_scope_type",
    "required_platform_scope_identities",
    "readiness_matrix_ref",
    "owner_review_to_canary_handoff_ref",
    "conflict_state",
    "schema_state",
    "target_match_state",
    "platform_scope_match_state",
    "platform_specific_readiness_placeholder_only_flag",
    "real_platform_readiness_created_flag",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "auto_canary_eligibility_claimed_flag",
    "connector_semantics_created_flag",
    "production_connector_semantic_values_populated_flag",
    "live_api_reachability_created_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "three_venue_canary_eligibility_green_flag",
    "limited_live_canary_execution_created_flag",
    "direct_limited_live_canary_execution_allowed_flag",
    "direct_live_order_router_allowed_flag",
    "direct_live_arbitrage_allowed_flag",
    "direct_full_scaled_live_allowed_flag",
    "direct_canary_execution_claimed_flag",
    "canary_execution_receipt_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

PLATFORM_ENTRY_FIELDS = {
    "platform_id",
    "readiness_state",
    "synthetic_placeholder_only_flag",
    "non_live_flag",
    "non_execution_flag",
    "source_required_flag",
    "future_gate_required_flag",
    "connector_semantics_created_flag",
    "live_api_reachability_created_flag",
    "balance_receipt_created_flag",
    "order_placement_authority_created_flag",
    "live_market_selection_created_flag",
    "runtime_cash_claim_created_flag",
}

READINESS_MATRIX_FIELDS = {
    "three_venue_platform_readiness_matrix_type",
    "three_venue_platform_readiness_matrix_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "platform_scope_type",
    "platform_scope_identities",
    "all_three_platforms_required_flag",
    "platform_readiness_entries",
    "matrix_entries_non_live_flag",
    "matrix_entries_non_execution_flag",
    "silent_single_venue_fallback_allowed_flag",
    "partial_platform_launch_allowed_flag",
    "partial_platform_launch_requires_future_owner_risk_reduction_override_flag",
    "future_owner_risk_reduction_override_present_flag",
    "connector_semantics_created_flag",
    "production_connector_semantic_values_populated_flag",
    "live_api_reachability_created_flag",
    "order_placement_authority_created_flag",
    "live_market_selection_created_flag",
    "runtime_cash_claim_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

HANDOFF_FIELDS = {
    "owner_review_to_canary_eligibility_handoff_type",
    "owner_review_to_canary_eligibility_handoff_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "three_venue_canary_eligibility_green_next_allowed_consumer",
    "canary_eligibility_gate_output_scope",
    "canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag",
    "direct_limited_live_canary_execution_allowed_flag",
    "direct_live_order_router_allowed_flag",
    "direct_live_arbitrage_allowed_flag",
    "direct_full_scaled_live_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "three_venue_canary_eligibility_green_flag",
    "limited_live_canary_execution_created_flag",
    "canary_execution_receipt_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

EXECUTION_BLOCK_FIELDS = {
    "limited_live_canary_execution_block_type",
    "limited_live_canary_execution_block_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "limited_live_canary_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "canary_execution_receipt_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

CASE_FIELDS = {
    "case_record_type",
    "case_id",
    "fixture_case",
    "case_authority_class",
    "synthetic_data_notice",
    "owner_live_promotion_review_gate_report_state",
    "owner_approval_receipt_boundary_state",
    "owner_review_freshness_state",
    "conflict_state",
    "schema_state",
    "target_match_state",
    "platform_scope_identities",
    "platform_scope_match_state",
    "silent_single_venue_fallback_claimed_flag",
    "partial_platform_silent_fallback_claimed_flag",
    "claim_attempt_type",
    "expected_gate_state",
    "blocker_codes",
    "receipt_ids",
}

FIXTURE_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "example_authority_class",
    "mode",
    "execution",
    "synthetic_data_notice",
    "fixture_no_claim_flags",
    "no_claim_flags",
    "validation_hook_ids",
    "three_venue_canary_eligibility_input_contract_records",
    "three_venue_platform_readiness_matrix_records",
    "owner_review_to_canary_eligibility_handoff_records",
    "limited_live_canary_execution_block_records",
    "three_venue_canary_eligibility_gate_case_records",
}

REPORT_FIELDS = {
    "report_type",
    "report_version",
    "master_plan_edition",
    "master_plan_sha256",
    "created_at_utc",
    "input_contract_record_count",
    "readiness_matrix_record_count",
    "handoff_record_count",
    "execution_block_record_count",
    "gate_case_record_count",
    "blocked_owner_review_or_approval_case_count",
    "blocked_platform_scope_case_count",
    "blocked_fallback_case_count",
    "blocked_execution_live_cash_profit_case_count",
    "blocked_atomicrows_or_blocker_reduction_case_count",
    "gate_state",
    "validation_failure_count",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "three_venue_canary_eligibility_green_next_allowed_consumer",
    "platform_scope_type",
    "required_platform_scope_identities",
    "canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag",
    "direct_limited_live_canary_execution_allowed_flag",
    "direct_live_order_router_allowed_flag",
    "direct_live_arbitrage_allowed_flag",
    "direct_full_scaled_live_allowed_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "three_venue_canary_eligibility_green_flag",
    "limited_live_canary_execution_allowed_flag",
    "limited_live_canary_execution_created_flag",
    "canary_execution_receipt_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "blocker_codes",
    "receipt_ids_emitted",
    "no_claim_flags",
    "validation_hook_ids",
}

SCHEMA_SPECS = {
    "input_contract": {
        "type_field": "three_venue_canary_eligibility_input_contract_type",
        "type_value": INPUT_CONTRACT_TYPE,
        "required": INPUT_CONTRACT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS),
        "true_fields": TRUE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS),
    },
    "readiness_matrix": {
        "type_field": "three_venue_platform_readiness_matrix_type",
        "type_value": READINESS_MATRIX_TYPE,
        "required": READINESS_MATRIX_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(READINESS_MATRIX_FIELDS),
        "true_fields": TRUE_BOUNDARY_FIELDS.intersection(READINESS_MATRIX_FIELDS),
    },
    "handoff": {
        "type_field": "owner_review_to_canary_eligibility_handoff_type",
        "type_value": HANDOFF_TYPE,
        "required": HANDOFF_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(HANDOFF_FIELDS),
        "true_fields": {
            "canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag"
        },
    },
    "gate_report": {
        "type_field": "report_type",
        "type_value": GATE_REPORT_TYPE,
        "required": REPORT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(REPORT_FIELDS),
        "true_fields": {
            "canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag"
        },
    },
    "execution_block": {
        "type_field": "limited_live_canary_execution_block_type",
        "type_value": EXECUTION_BLOCK_TYPE,
        "required": EXECUTION_BLOCK_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(EXECUTION_BLOCK_FIELDS),
        "true_fields": set(),
    },
}

EXPECTED_STATE_BY_CASE = {
    "BLOCKED_MISSING_OWNER_LIVE_PROMOTION_REVIEW_GATE_REPORT": (
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_GATE_REPORT_MISSING"
    ),
    "BLOCKED_MISSING_OWNER_APPROVAL_RECEIPT_BOUNDARY": (
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_APPROVAL_RECEIPT_BOUNDARY_MISSING"
    ),
    "BLOCKED_STALE_OWNER_REVIEW_REPORT": "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_STALE",
    "BLOCKED_SUPERSEDED_OWNER_REVIEW_REPORT": (
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_SUPERSEDED"
    ),
    "BLOCKED_CONFLICT_STATE": "BLOCKED_CANARY_ELIGIBILITY_CONFLICT_STATE",
    "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_CANARY_ELIGIBILITY_SCHEMA_ERROR",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_CANARY_ELIGIBILITY_TARGET_MISMATCH",
    "BLOCKED_PLATFORM_MISSING_KALSHI": "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_KALSHI_MISSING",
    "BLOCKED_PLATFORM_MISSING_POLYMARKET": (
        "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_POLYMARKET_MISSING"
    ),
    "BLOCKED_PLATFORM_MISSING_FORECASTEX_IBKR": (
        "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_FORECASTEX_IBKR_MISSING"
    ),
    "BLOCKED_NONCANONICAL_THIRD_VENUE_IDENTITY": (
        "BLOCKED_CANARY_ELIGIBILITY_NONCANONICAL_THIRD_VENUE"
    ),
    "BLOCKED_SINGLE_VENUE_FALLBACK_CLAIM": (
        "BLOCKED_CANARY_ELIGIBILITY_SINGLE_VENUE_FALLBACK_CLAIM"
    ),
    "BLOCKED_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM": (
        "BLOCKED_CANARY_ELIGIBILITY_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM"
    ),
    "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM": (
        "BLOCKED_CANARY_ELIGIBILITY_DIRECT_CANARY_EXECUTION_CLAIM"
    ),
    "BLOCKED_LIVE_REACHABILITY_CLAIM": "BLOCKED_CANARY_ELIGIBILITY_LIVE_REACHABILITY_CLAIM",
    "BLOCKED_ORDER_EXECUTION_CLAIM": "BLOCKED_CANARY_ELIGIBILITY_ORDER_EXECUTION_CLAIM",
    "BLOCKED_RUNTIME_CASH_PROFIT_CLAIM": (
        "BLOCKED_CANARY_ELIGIBILITY_RUNTIME_CASH_PROFIT_CLAIM"
    ),
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": (
        "BLOCKED_CANARY_ELIGIBILITY_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM"
    ),
    "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKED_CANARY_ELIGIBILITY_BLOCKER_REDUCTION_CLAIM",
}

REQUIRED_FIXTURE_CASES = {
    "VALID_SYNTHETIC_STATIC_THREE_VENUE_CANARY_ELIGIBILITY_INPUT_CONTRACT",
    "VALID_SYNTHETIC_BLOCKED_THREE_VENUE_PLATFORM_READINESS_MATRIX",
    "VALID_SYNTHETIC_OWNER_REVIEW_TO_CANARY_ELIGIBILITY_HANDOFF_BLOCK",
    "VALID_SYNTHETIC_LIMITED_LIVE_CANARY_EXECUTION_BLOCK",
    *EXPECTED_STATE_BY_CASE,
}

CLAIM_STATE_BY_TYPE = {
    "NONE": None,
    "DIRECT_CANARY_EXECUTION": "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM",
    "LIVE_REACHABILITY": "BLOCKED_LIVE_REACHABILITY_CLAIM",
    "ORDER_EXECUTION": "BLOCKED_ORDER_EXECUTION_CLAIM",
    "RUNTIME_CASH_PROFIT": "BLOCKED_RUNTIME_CASH_PROFIT_CLAIM",
    "ATOMICROWS_BUNDLE_HASH_MUTATION": "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKER_REDUCTION": "BLOCKED_BLOCKER_REDUCTION_CLAIM",
}


def _master_plan_sha256(path: pathlib.Path) -> str:
    if not path.exists():
        return "0" * 64
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _const(schema: dict[str, Any], field: str) -> Any:
    prop = _properties(schema).get(field)
    return prop.get("const") if isinstance(prop, dict) else None


def _required(schema: dict[str, Any]) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _validate_blockers(value: Any, label: str, *, required: bool = True) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list"]
    if required and not value:
        return [f"{label} must not be empty"]
    if len(value) != len(set(value)):
        return [f"{label} must not contain duplicates"]
    return [
        f"{label}[{index}] must be a non-empty string"
        for index, item in enumerate(value)
        if not _is_non_empty_string(item)
    ]


def _validate_receipts(value: Any, label: str) -> list[str]:
    return _validate_blockers(value, label, required=True)


def _validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures = true_claim_failures(
        value,
        forbidden_true_fields=FORBIDDEN_TRUE_FIELDS,
        label=label,
    )
    for path, key, item in _walk(value, label):
        if key in FORBIDDEN_COUNT_FIELDS and item != 0:
            failures.append(f"{path} must be 0")
    return failures


def _walk(value: Any, path: str = "value"):
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


def _platform_scope_failures(value: Any, label: str) -> list[str]:
    if value != CANONICAL_PLATFORMS:
        return [f"{label} must be exactly {CANONICAL_PLATFORMS}"]
    return []


def _validate_common_static_record(record: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    failures.extend(require_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_validate_no_forbidden_claims(record, label))
    return failures


def validate_schema(
    schema: dict[str, Any],
    *,
    schema_key: str,
    schema_path: pathlib.Path | None = None,
) -> list[str]:
    label = str(schema_path or schema_key)
    spec = SCHEMA_SPECS[schema_key]
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{label} must be an object schema")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{label} must be closed with additionalProperties=false")
    if _required(schema) != set(spec["required"]):
        missing = sorted(set(spec["required"]) - _required(schema))
        extra = sorted(_required(schema) - set(spec["required"]))
        if missing:
            failures.append(f"{label}.required missing fields: {', '.join(missing)}")
        if extra:
            failures.append(f"{label}.required has unexpected fields: {', '.join(extra)}")
    if _const(schema, spec["type_field"]) != spec["type_value"]:
        failures.append(f"{label}.{spec['type_field']} const must be {spec['type_value']}")
    for field in sorted(spec["false_fields"]):
        if _const(schema, field) is not False:
            failures.append(f"{label}.{field} const must be false")
    for field in sorted(spec["true_fields"]):
        if _const(schema, field) is not True:
            failures.append(f"{label}.{field} const must be true")
    return failures


def _require_exact_fields(record: dict[str, Any], fields: set[str], label: str) -> list[str]:
    return require_exact_fields(record, fields, label)


def validate_input_contract_record(
    record: dict[str, Any],
    *,
    label: str = "three-venue canary eligibility input contract",
) -> list[str]:
    failures = _require_exact_fields(record, INPUT_CONTRACT_FIELDS, label)
    if record.get("three_venue_canary_eligibility_input_contract_type") != INPUT_CONTRACT_TYPE:
        failures.append(f"{label}.three_venue_canary_eligibility_input_contract_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_THREE_VENUE_CANARY_ELIGIBILITY_INPUT_CONTRACT_ONLY_NOT_CANARY_ELIGIBILITY_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static canary input only")
    for field in [
        "owner_live_promotion_review_gate_report_ref",
        "owner_live_promotion_review_gate_report_digest",
        "owner_approval_receipt_boundary_ref",
        "owner_approval_receipt_boundary_digest",
        "readiness_matrix_ref",
        "owner_review_to_canary_handoff_ref",
    ]:
        if not _is_non_empty_string(record.get(field)):
            failures.append(f"{label}.{field} must be present")
    if record.get("owner_live_promotion_review_gate_report_state") != (
        "PRESENT_IMMUTABLE_PASS_THREE_VENUE_CANARY_ELIGIBILITY_REQUIRED"
    ):
        failures.append(
            f"{label}.owner_live_promotion_review_gate_report_state must be present immutable pass"
        )
    if record.get("owner_approval_receipt_boundary_state") != "PRESENT_IMMUTABLE_REQUIRED":
        failures.append(f"{label}.owner_approval_receipt_boundary_state must be PRESENT_IMMUTABLE_REQUIRED")
    if record.get("owner_review_freshness_state") != "FRESH":
        failures.append(f"{label}.owner_review_freshness_state must be FRESH")
    if record.get("owner_live_promotion_review_pass_next_allowed_consumer") != (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    ):
        failures.append(
            f"{label}.owner_live_promotion_review_pass_next_allowed_consumer must be "
            f"{OWNER_REVIEW_TO_CANARY_CONSUMER}"
        )
    if record.get("platform_scope_type") != PLATFORM_SCOPE_TYPE:
        failures.append(f"{label}.platform_scope_type must be {PLATFORM_SCOPE_TYPE}")
    failures.extend(
        _platform_scope_failures(
            record.get("required_platform_scope_identities"),
            f"{label}.required_platform_scope_identities",
        )
    )
    for field, expected in [
        ("conflict_state", "NO_CONFLICT"),
        ("schema_state", "SCHEMA_VALID"),
        ("target_match_state", "MATCH"),
        ("platform_scope_match_state", "MATCH"),
    ]:
        if record.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    for field in sorted(TRUE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS)):
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", required=False))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_readiness_matrix_record(
    record: dict[str, Any],
    *,
    label: str = "three-venue platform readiness matrix",
) -> list[str]:
    failures = _require_exact_fields(record, READINESS_MATRIX_FIELDS, label)
    if record.get("three_venue_platform_readiness_matrix_type") != READINESS_MATRIX_TYPE:
        failures.append(f"{label}.three_venue_platform_readiness_matrix_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_THREE_VENUE_PLATFORM_READINESS_MATRIX_ONLY_NOT_LIVE_READINESS_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static matrix only")
    if record.get("platform_scope_type") != PLATFORM_SCOPE_TYPE:
        failures.append(f"{label}.platform_scope_type must be {PLATFORM_SCOPE_TYPE}")
    failures.extend(_platform_scope_failures(record.get("platform_scope_identities"), f"{label}.platform_scope_identities"))

    entries = record.get("platform_readiness_entries")
    if not isinstance(entries, list) or len(entries) != 3:
        failures.append(f"{label}.platform_readiness_entries must contain exactly three entries")
        entries = []
    seen_platforms: list[str] = []
    for index, entry in enumerate(entries):
        entry_label = f"{label}.platform_readiness_entries[{index}]"
        if not isinstance(entry, dict):
            failures.append(f"{entry_label} must be an object")
            continue
        failures.extend(require_exact_fields(entry, PLATFORM_ENTRY_FIELDS, entry_label))
        platform_id = entry.get("platform_id")
        seen_platforms.append(str(platform_id))
        if platform_id not in CANONICAL_PLATFORMS:
            failures.append(f"{entry_label}.platform_id must be canonical")
        if entry.get("readiness_state") not in {
            "BLOCKED_STATIC_CONTRACT_ONLY",
            "SOURCE_REQUIRED",
            "FUTURE_GATE_REQUIRED",
        }:
            failures.append(f"{entry_label}.readiness_state must remain blocked/static/source/future")
        for field in [
            "synthetic_placeholder_only_flag",
            "non_live_flag",
            "non_execution_flag",
            "source_required_flag",
            "future_gate_required_flag",
        ]:
            if entry.get(field) is not True:
                failures.append(f"{entry_label}.{field} must be true")
        for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(PLATFORM_ENTRY_FIELDS)):
            if entry.get(field) is not False:
                failures.append(f"{entry_label}.{field} must be false")
    if sorted(seen_platforms) != sorted(CANONICAL_PLATFORMS):
        failures.append(f"{label}.platform_readiness_entries must cover all canonical platforms")

    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(READINESS_MATRIX_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    for field in sorted(TRUE_BOUNDARY_FIELDS.intersection(READINESS_MATRIX_FIELDS)):
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_handoff_record(
    record: dict[str, Any],
    *,
    label: str = "owner-review-to-canary handoff",
) -> list[str]:
    failures = _require_exact_fields(record, HANDOFF_FIELDS, label)
    if record.get("owner_review_to_canary_eligibility_handoff_type") != HANDOFF_TYPE:
        failures.append(f"{label}.owner_review_to_canary_eligibility_handoff_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_OWNER_REVIEW_TO_CANARY_ELIGIBILITY_HANDOFF_ONLY_NOT_EXECUTION_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static handoff only")
    if record.get("owner_live_promotion_review_pass_next_allowed_consumer") != (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    ):
        failures.append(
            f"{label}.owner_live_promotion_review_pass_next_allowed_consumer must be "
            f"{OWNER_REVIEW_TO_CANARY_CONSUMER}"
        )
    if record.get("three_venue_canary_eligibility_green_next_allowed_consumer") != (
        LIMITED_LIVE_BOUNDARY_CONSUMER
    ):
        failures.append(
            f"{label}.three_venue_canary_eligibility_green_next_allowed_consumer must be "
            f"{LIMITED_LIVE_BOUNDARY_CONSUMER}"
        )
    if record.get("canary_eligibility_gate_output_scope") != "STATIC_BLOCKED_READINESS_REPORTS_ONLY":
        failures.append(f"{label}.canary_eligibility_gate_output_scope must be static blocked reports only")
    if (
        record.get("canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag")
        is not True
    ):
        failures.append(
            f"{label}.canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag "
            "must be true"
        )
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(HANDOFF_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_execution_block_record(
    record: dict[str, Any],
    *,
    label: str = "limited-live canary execution block",
) -> list[str]:
    failures = _require_exact_fields(record, EXECUTION_BLOCK_FIELDS, label)
    if record.get("limited_live_canary_execution_block_type") != EXECUTION_BLOCK_TYPE:
        failures.append(f"{label}.limited_live_canary_execution_block_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_LIMITED_LIVE_CANARY_EXECUTION_BLOCK_ONLY_NO_EXECUTION_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static execution block only")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(EXECUTION_BLOCK_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_gate_case_record(
    record: dict[str, Any],
    *,
    label: str = "three-venue canary eligibility gate case",
) -> list[str]:
    failures = _require_exact_fields(record, CASE_FIELDS, label)
    if record.get("case_record_type") != "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_GATE_CASE":
        failures.append(f"{label}.case_record_type is invalid")
    if record.get("case_authority_class") != (
        "SYNTHETIC_CASE_ONLY_NOT_THREE_VENUE_CANARY_ELIGIBILITY_AUTHORITY"
    ):
        failures.append(f"{label}.case_authority_class must be synthetic case only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")

    case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR46 case")
    elif record.get("expected_gate_state") != expected_state:
        failures.append(f"{label}.expected_gate_state must be {expected_state}")

    state_expectations = {
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_GATE_REPORT_MISSING": (
            record.get("owner_live_promotion_review_gate_report_state") == "MISSING"
        ),
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_APPROVAL_RECEIPT_BOUNDARY_MISSING": (
            record.get("owner_approval_receipt_boundary_state") == "MISSING"
        ),
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_STALE": (
            record.get("owner_review_freshness_state") == "STALE"
        ),
        "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_SUPERSEDED": (
            record.get("owner_review_freshness_state") == "SUPERSEDED"
        ),
        "BLOCKED_CANARY_ELIGIBILITY_CONFLICT_STATE": (
            record.get("conflict_state") == "CONFLICT_PRESENT"
        ),
        "BLOCKED_CANARY_ELIGIBILITY_SCHEMA_ERROR": record.get("schema_state") == "SCHEMA_ERROR",
        "BLOCKED_CANARY_ELIGIBILITY_TARGET_MISMATCH": record.get("target_match_state") == "MISMATCH",
        "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_KALSHI_MISSING": (
            "KALSHI" not in record.get("platform_scope_identities", [])
        ),
        "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_POLYMARKET_MISSING": (
            "POLYMARKET" not in record.get("platform_scope_identities", [])
        ),
        "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_FORECASTEX_IBKR_MISSING": (
            "FORECASTEX_IBKR" not in record.get("platform_scope_identities", [])
        ),
        "BLOCKED_CANARY_ELIGIBILITY_NONCANONICAL_THIRD_VENUE": (
            record.get("platform_scope_identities") != CANONICAL_PLATFORMS
        ),
        "BLOCKED_CANARY_ELIGIBILITY_SINGLE_VENUE_FALLBACK_CLAIM": (
            record.get("silent_single_venue_fallback_claimed_flag") is True
        ),
        "BLOCKED_CANARY_ELIGIBILITY_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM": (
            record.get("partial_platform_silent_fallback_claimed_flag") is True
        ),
    }
    if expected_state in state_expectations and not state_expectations[expected_state]:
        failures.append(f"{label}.{case} state fields do not match expected blocked state")

    claim_type = record.get("claim_attempt_type")
    if claim_type not in CLAIM_STATE_BY_TYPE:
        failures.append(f"{label}.claim_attempt_type is invalid")
    else:
        claim_case = CLAIM_STATE_BY_TYPE[claim_type]
        if claim_case is None:
            claim_cases = {
                "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM",
                "BLOCKED_LIVE_REACHABILITY_CLAIM",
                "BLOCKED_ORDER_EXECUTION_CLAIM",
                "BLOCKED_RUNTIME_CASH_PROFIT_CLAIM",
                "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
                "BLOCKED_BLOCKER_REDUCTION_CLAIM",
            }
            if case in claim_cases:
                failures.append(f"{label}.claim_attempt_type must explain blocked claim case")
        elif case != claim_case:
            failures.append(f"{label}.claim_attempt_type does not match fixture_case")

    if record.get("platform_scope_match_state") not in {"MATCH", "MISMATCH"}:
        failures.append(f"{label}.platform_scope_match_state is invalid")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = _require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_CANARY_ELIGIBILITY_NOT_SOURCE_FACT"
    ):
        failures.append("fixture.fixture_authority_class must be synthetic canary non-authority")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_OWNER_APPROVAL_NOT_CANARY_ELIGIBILITY_NOT_EXECUTION"
    ):
        failures.append("fixture.example_authority_class must be synthetic static only")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append("fixture.synthetic_data_notice must mark synthetic non-authority")
    failures.extend(require_bool_map(fixture.get("fixture_no_claim_flags"), NO_CLAIM_FLAGS, "fixture.fixture_no_claim_flags"))
    failures.extend(require_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "fixture.no_claim_flags"))
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_validate_no_forbidden_claims(fixture, "fixture"))

    groups = {
        "three_venue_canary_eligibility_input_contract_records": fixture.get(
            "three_venue_canary_eligibility_input_contract_records"
        ),
        "three_venue_platform_readiness_matrix_records": fixture.get(
            "three_venue_platform_readiness_matrix_records"
        ),
        "owner_review_to_canary_eligibility_handoff_records": fixture.get(
            "owner_review_to_canary_eligibility_handoff_records"
        ),
        "limited_live_canary_execution_block_records": fixture.get(
            "limited_live_canary_execution_block_records"
        ),
        "three_venue_canary_eligibility_gate_case_records": fixture.get(
            "three_venue_canary_eligibility_gate_case_records"
        ),
    }
    for name, records in groups.items():
        if not isinstance(records, list) or not records:
            failures.append(f"fixture.{name} must be a non-empty list")
            groups[name] = []

    seen_cases: set[str] = set()
    validators = {
        "three_venue_canary_eligibility_input_contract_records": validate_input_contract_record,
        "three_venue_platform_readiness_matrix_records": validate_readiness_matrix_record,
        "owner_review_to_canary_eligibility_handoff_records": validate_handoff_record,
        "limited_live_canary_execution_block_records": validate_execution_block_record,
        "three_venue_canary_eligibility_gate_case_records": validate_gate_case_record,
    }
    for group_name, validator in validators.items():
        for index, record in enumerate(groups[group_name]):
            if not isinstance(record, dict):
                failures.append(f"{group_name}[{index}] must be an object")
                continue
            seen_cases.add(str(record.get("fixture_case")))
            failures.extend(validator(record, label=f"{group_name}[{index}]"))

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - seen_cases)
    if missing_cases:
        failures.append(f"fixture missing required PR46 cases: {', '.join(missing_cases)}")
    failures.extend(validate_current_atomicrows_bundle_state(repo_root, label="PR46 three-venue canary fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    input_contract_schema_path: pathlib.Path = DEFAULT_INPUT_CONTRACT_SCHEMA,
    readiness_matrix_schema_path: pathlib.Path = DEFAULT_READINESS_MATRIX_SCHEMA,
    handoff_schema_path: pathlib.Path = DEFAULT_HANDOFF_SCHEMA,
    gate_report_schema_path: pathlib.Path = DEFAULT_GATE_REPORT_SCHEMA,
    execution_block_schema_path: pathlib.Path = DEFAULT_EXECUTION_BLOCK_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schema_paths = {
        "input_contract": input_contract_schema_path,
        "readiness_matrix": readiness_matrix_schema_path,
        "handoff": handoff_schema_path,
        "gate_report": gate_report_schema_path,
        "execution_block": execution_block_schema_path,
    }
    for key, path in schema_paths.items():
        schema, schema_failures = load_json_object(path)
        failures.extend(schema_failures)
        if schema is not None:
            failures.extend(validate_schema(schema, schema_key=key, schema_path=path))

    fixture, fixture_failures = load_json_object(fixture_path)
    failures.extend(fixture_failures)
    if fixture is not None:
        failures.extend(validate_fixture(fixture, repo_root=repo_root))
    failures.extend(validate_current_atomicrows_bundle_state(repo_root, label="PR46 three-venue canary validator"))
    return failures


def _case_counts(cases: Sequence[Any]) -> dict[str, int]:
    counts = {
        "blocked_owner_review_or_approval_case_count": 0,
        "blocked_platform_scope_case_count": 0,
        "blocked_fallback_case_count": 0,
        "blocked_execution_live_cash_profit_case_count": 0,
        "blocked_atomicrows_or_blocker_reduction_case_count": 0,
    }
    for record in cases:
        if not isinstance(record, dict):
            continue
        case = record.get("fixture_case")
        if case in {
            "BLOCKED_MISSING_OWNER_LIVE_PROMOTION_REVIEW_GATE_REPORT",
            "BLOCKED_MISSING_OWNER_APPROVAL_RECEIPT_BOUNDARY",
            "BLOCKED_STALE_OWNER_REVIEW_REPORT",
            "BLOCKED_SUPERSEDED_OWNER_REVIEW_REPORT",
            "BLOCKED_CONFLICT_STATE",
            "BLOCKED_SCHEMA_ERROR_STATE",
            "BLOCKED_TARGET_MISMATCH",
        }:
            counts["blocked_owner_review_or_approval_case_count"] += 1
        if case in {
            "BLOCKED_PLATFORM_MISSING_KALSHI",
            "BLOCKED_PLATFORM_MISSING_POLYMARKET",
            "BLOCKED_PLATFORM_MISSING_FORECASTEX_IBKR",
            "BLOCKED_NONCANONICAL_THIRD_VENUE_IDENTITY",
        }:
            counts["blocked_platform_scope_case_count"] += 1
        if case in {
            "BLOCKED_SINGLE_VENUE_FALLBACK_CLAIM",
            "BLOCKED_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM",
        }:
            counts["blocked_fallback_case_count"] += 1
        if case in {
            "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM",
            "BLOCKED_LIVE_REACHABILITY_CLAIM",
            "BLOCKED_ORDER_EXECUTION_CLAIM",
            "BLOCKED_RUNTIME_CASH_PROFIT_CLAIM",
        }:
            counts["blocked_execution_live_cash_profit_case_count"] += 1
        if case in {
            "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
            "BLOCKED_BLOCKER_REDUCTION_CLAIM",
        }:
            counts["blocked_atomicrows_or_blocker_reduction_case_count"] += 1
    return counts


def _all_fixture_records(fixture: dict[str, Any] | None) -> list[Any]:
    if fixture is None:
        return []
    records: list[Any] = []
    for key in [
        "three_venue_canary_eligibility_input_contract_records",
        "three_venue_platform_readiness_matrix_records",
        "owner_review_to_canary_eligibility_handoff_records",
        "limited_live_canary_execution_block_records",
        "three_venue_canary_eligibility_gate_case_records",
    ]:
        value = fixture.get(key, [])
        if isinstance(value, list):
            records.extend(value)
    return records


def build_report(
    *,
    fixture: dict[str, Any] | None,
    repo_root: pathlib.Path,
    validation_failures: Sequence[str],
    master_plan_path: pathlib.Path = DEFAULT_MASTER_PLAN,
) -> dict[str, Any]:
    inputs = fixture.get("three_venue_canary_eligibility_input_contract_records", []) if fixture else []
    matrices = fixture.get("three_venue_platform_readiness_matrix_records", []) if fixture else []
    handoffs = fixture.get("owner_review_to_canary_eligibility_handoff_records", []) if fixture else []
    blocks = fixture.get("limited_live_canary_execution_block_records", []) if fixture else []
    cases = fixture.get("three_venue_canary_eligibility_gate_case_records", []) if fixture else []
    records = _all_fixture_records(fixture)
    blocker_codes = sorted(
        {
            blocker
            for record in records
            if isinstance(record, dict)
            for blocker in record.get("blocker_codes", [])
            if isinstance(blocker, str)
        }
    )
    receipt_ids = sorted(
        {
            receipt
            for record in records
            if isinstance(record, dict)
            for receipt in record.get("receipt_ids", [])
            if isinstance(receipt, str)
        }
    )
    return {
        "report_type": GATE_REPORT_TYPE,
        "report_version": "PR46_STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_REPORT_V1",
        "master_plan_edition": "v9.9.746",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "input_contract_record_count": len(inputs),
        "readiness_matrix_record_count": len(matrices),
        "handoff_record_count": len(handoffs),
        "execution_block_record_count": len(blocks),
        "gate_case_record_count": len(cases),
        **_case_counts(cases),
        "gate_state": "FAIL" if validation_failures else STATIC_GATE_STATE,
        "validation_failure_count": len(validation_failures),
        "owner_live_promotion_review_pass_next_allowed_consumer": OWNER_REVIEW_TO_CANARY_CONSUMER,
        "three_venue_canary_eligibility_green_next_allowed_consumer": LIMITED_LIVE_BOUNDARY_CONSUMER,
        "platform_scope_type": PLATFORM_SCOPE_TYPE,
        "required_platform_scope_identities": list(CANONICAL_PLATFORMS),
        "canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag": True,
        "direct_limited_live_canary_execution_allowed_flag": False,
        "direct_live_order_router_allowed_flag": False,
        "direct_live_arbitrage_allowed_flag": False,
        "direct_full_scaled_live_allowed_flag": False,
        "live_eligibility_allowed_flag": False,
        "three_venue_canary_eligibility_allowed_flag": False,
        "three_venue_canary_eligibility_created_flag": False,
        "three_venue_canary_eligibility_green_flag": False,
        "limited_live_canary_execution_allowed_flag": False,
        "limited_live_canary_execution_created_flag": False,
        "canary_execution_receipt_created_flag": False,
        "live_reachability_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "runtime_cash_claim_allowed_flag": False,
        "profit_claim_allowed_flag": False,
        "atomicrows_bundle_hash_created_or_mutated_flag": False,
        "blocker_reduction_claim_created_flag": False,
        "blocker_codes": blocker_codes,
        "receipt_ids_emitted": receipt_ids,
        "no_claim_flags": dict(NO_CLAIM_FLAGS),
        "validation_hook_ids": [VALIDATION_HOOK],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-contract-schema", default=str(DEFAULT_INPUT_CONTRACT_SCHEMA))
    parser.add_argument("--readiness-matrix-schema", default=str(DEFAULT_READINESS_MATRIX_SCHEMA))
    parser.add_argument("--handoff-schema", default=str(DEFAULT_HANDOFF_SCHEMA))
    parser.add_argument("--gate-report-schema", default=str(DEFAULT_GATE_REPORT_SCHEMA))
    parser.add_argument("--execution-block-schema", default=str(DEFAULT_EXECUTION_BLOCK_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = pathlib.Path(args.repo_root)
    fixture_path = pathlib.Path(args.fixture)
    fixture, fixture_load_failures = load_json_object(fixture_path)
    failures = validate_static_surface(
        repo_root=repo_root,
        input_contract_schema_path=pathlib.Path(args.input_contract_schema),
        readiness_matrix_schema_path=pathlib.Path(args.readiness_matrix_schema),
        handoff_schema_path=pathlib.Path(args.handoff_schema),
        gate_report_schema_path=pathlib.Path(args.gate_report_schema),
        execution_block_schema_path=pathlib.Path(args.execution_block_schema),
        fixture_path=fixture_path,
    )
    failures.extend(fixture_load_failures)
    report = build_report(fixture=fixture, repo_root=repo_root, validation_failures=failures)
    if args.out:
        write_json(repo_root / pathlib.Path(args.out), report)
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
