#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any, Iterable, Sequence

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from qtt.core.testing.gate_result import (  # noqa: E402
    load_json_object,
    require_bool_map,
    require_exact_fields,
    validate_current_atomicrows_bundle_state,
    write_json,
)

SUCCESS_MARKER = "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_OK"
FAILURE_MARKER = "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_STATIC_AUDIT"

INPUT_CONTRACT_TYPE = "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_INPUT_CONTRACT"
OWNER_APPROVAL_RECEIPT_BOUNDARY_TYPE = "STAGE1_OWNER_APPROVAL_RECEIPT_BOUNDARY"
GATE_REPORT_TYPE = "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_GATE_REPORT"
HANDOFF_BLOCK_TYPE = "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_HANDOFF_BLOCK"

EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
STATIC_GATE_STATE = "STATIC_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
OWNER_REVIEW_ONLY_CONSUMER = "OWNER_LIVE_PROMOTION_REVIEW_ONLY"
THREE_VENUE_CANARY_GATE_ONLY_CONSUMER = "THREE_VENUE_CANARY_ELIGIBILITY_GATE_ONLY"

DEFAULT_INPUT_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_owner_live_promotion_review_input_contract.schema.json"
)
DEFAULT_OWNER_APPROVAL_RECEIPT_BOUNDARY_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_owner_approval_receipt_boundary.schema.json"
)
DEFAULT_GATE_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_owner_live_promotion_review_gate_report.schema.json"
)
DEFAULT_HANDOFF_BLOCK_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/owner_live_promotion_review/"
    "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
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
    "auto_live_promotion_claimed_flag",
    "blocker_reduction_claim_allowed_flag",
    "blocker_reduction_claim_created_flag",
    "direct_canary_eligibility_claimed_flag",
    "direct_canary_execution_claimed_flag",
    "dual_result_review_decision_created_flag",
    "live_eligibility_allowed_flag",
    "limited_live_canary_execution_created_flag",
    "order_execution_allowed_flag",
    "owner_approval_decision_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_approval_receipt_creation_claimed_flag",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "owner_live_promotion_review_decision_created_flag",
    "owner_live_promotion_review_direct_canary_eligibility_allowed",
    "owner_live_promotion_review_direct_canary_execution_allowed",
    "owner_live_promotion_review_direct_live_consumer_allowed",
    "owner_live_promotion_review_direct_order_router_allowed",
    "profit_claim_allowed_flag",
    "result_merge_claimed_flag",
    "runtime_cash_claim_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "three_venue_canary_eligibility_gate_created_flag",
    "live_reachability_allowed_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | FALSE_BOUNDARY_FIELDS | {
    "atomicrows_bundle_created",
    "atomicrows_hash_created",
    "auto_promotion_created",
    "blocker_reduction_claimed",
    "direct_canary_eligibility_created",
    "direct_canary_execution_created",
    "live_order_authority_created",
    "owner_approval_receipt_created",
    "owner_live_promotion_approval_created",
    "replay_paper_result_merge_created",
}

FORBIDDEN_COUNT_FIELDS = {
    "accepted_source_fact_created_count",
    "atomicrows_bundle_hash_mutation_claim_count",
    "auto_live_promotion_claim_count",
    "blocker_reduction_claim_count",
    "direct_canary_eligibility_claim_count",
    "direct_canary_execution_claim_count",
    "live_order_runtime_cash_profit_claim_count",
    "owner_approval_receipt_created_count",
    "owner_live_promotion_approval_created_count",
    "result_merge_claim_count",
}

INPUT_CONTRACT_FIELDS = {
    "owner_live_promotion_review_input_contract_type",
    "owner_live_promotion_review_input_contract_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "dual_result_review_gate_report_ref",
    "dual_result_review_gate_report_digest",
    "dual_result_review_gate_report_state",
    "dual_result_review_state",
    "dual_result_review_input_identity_digest",
    "replay_result_packet_boundary_ref",
    "paper_result_packet_boundary_ref",
    "replay_result_packet_boundary_digest",
    "paper_result_packet_boundary_digest",
    "replay_paper_result_boundaries_separate_flag",
    "runtime_resolver_snapshot_id",
    "dual_result_runtime_resolver_snapshot_id",
    "replay_runtime_resolver_snapshot_id",
    "paper_runtime_resolver_snapshot_id",
    "runtime_resolver_snapshot_digest",
    "dual_result_runtime_resolver_snapshot_digest",
    "replay_runtime_resolver_snapshot_digest",
    "paper_runtime_resolver_snapshot_digest",
    "runtime_resolver_snapshot_identity_unchanged_flag",
    "upstream_report_references_immutable_flag",
    "upstream_receipt_references_immutable_flag",
    "input_identity_digest_state",
    "conflict_state",
    "schema_state",
    "lane_match_state",
    "target_match_state",
    "dual_result_review_pass_next_allowed_consumer",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "owner_review_required_after_dual_result_review_flag",
    "live_eligibility_requires_later_three_venue_canary_eligibility_gate",
    "result_merge_claimed_flag",
    "dual_result_review_decision_created_flag",
    "owner_live_promotion_review_decision_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_approval_receipt_creation_claimed_flag",
    "owner_live_promotion_review_direct_live_consumer_allowed",
    "owner_live_promotion_review_direct_order_router_allowed",
    "owner_live_promotion_review_direct_canary_execution_allowed",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "auto_live_promotion_claimed_flag",
    "direct_canary_eligibility_claimed_flag",
    "direct_canary_execution_claimed_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "limited_live_canary_execution_created_flag",
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

OWNER_APPROVAL_RECEIPT_BOUNDARY_FIELDS = {
    "owner_approval_receipt_boundary_type",
    "owner_approval_receipt_boundary_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "owner_approval_receipt_creation_authority_state",
    "owner_approval_receipt_created_flag",
    "owner_approval_decision_created_flag",
    "owner_approval_receipt_required_before_live_eligibility_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_allowed_flag",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

HANDOFF_BLOCK_FIELDS = {
    "three_venue_canary_eligibility_handoff_block_type",
    "three_venue_canary_eligibility_handoff_block_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "dual_result_review_pass_next_allowed_consumer",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "handoff_block_scope",
    "owner_live_promotion_review_direct_live_consumer_allowed",
    "owner_live_promotion_review_direct_order_router_allowed",
    "owner_live_promotion_review_direct_canary_execution_allowed",
    "owner_live_promotion_review_direct_canary_eligibility_allowed",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "live_eligibility_requires_later_three_venue_canary_eligibility_gate",
    "owner_approval_receipt_created_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_gate_created_flag",
    "three_venue_canary_eligibility_created_flag",
    "limited_live_canary_execution_created_flag",
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

CASE_FIELDS = {
    "case_record_type",
    "case_id",
    "fixture_case",
    "case_authority_class",
    "synthetic_data_notice",
    "dual_result_review_gate_report_state",
    "replay_result_boundary_reference_state",
    "paper_result_boundary_reference_state",
    "input_identity_digest_state",
    "conflict_state",
    "schema_state",
    "lane_match_state",
    "target_match_state",
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
    "owner_live_promotion_review_input_contract_records",
    "owner_approval_receipt_boundary_records",
    "three_venue_canary_eligibility_handoff_block_records",
    "owner_live_promotion_review_gate_case_records",
}

REPORT_FIELDS = {
    "report_type",
    "report_version",
    "master_plan_edition",
    "master_plan_sha256",
    "created_at_utc",
    "input_contract_record_count",
    "owner_approval_receipt_boundary_record_count",
    "three_venue_canary_handoff_block_record_count",
    "gate_case_record_count",
    "blocked_missing_dual_result_review_gate_case_count",
    "blocked_missing_replay_or_paper_boundary_case_count",
    "blocked_missing_digest_case_count",
    "blocked_stale_conflict_schema_lane_target_case_count",
    "blocked_result_merge_or_decision_case_count",
    "blocked_owner_approval_or_auto_promotion_case_count",
    "blocked_canary_shortcut_case_count",
    "blocked_live_cash_profit_atomicrows_case_count",
    "blocked_blocker_reduction_case_count",
    "gate_state",
    "validation_failure_count",
    "dual_result_review_pass_next_allowed_consumer",
    "owner_live_promotion_review_pass_next_allowed_consumer",
    "owner_live_promotion_review_direct_live_consumer_allowed",
    "owner_live_promotion_review_direct_order_router_allowed",
    "owner_live_promotion_review_direct_canary_execution_allowed",
    "owner_live_promotion_review_auto_approval_allowed",
    "owner_live_promotion_review_auto_promotion_allowed",
    "live_eligibility_requires_later_three_venue_canary_eligibility_gate",
    "owner_live_promotion_review_decision_created_flag",
    "owner_approval_receipt_created_flag",
    "live_eligibility_allowed_flag",
    "three_venue_canary_eligibility_allowed_flag",
    "three_venue_canary_eligibility_created_flag",
    "limited_live_canary_execution_created_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids_emitted",
    "no_claim_flags",
    "validation_hook_ids",
}

SCHEMA_SPECS = {
    "input_contract": {
        "type_field": "owner_live_promotion_review_input_contract_type",
        "type_value": INPUT_CONTRACT_TYPE,
        "required": INPUT_CONTRACT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS),
        "true_fields": {
            "live_eligibility_requires_later_three_venue_canary_eligibility_gate",
            "owner_review_required_after_dual_result_review_flag",
            "replay_paper_result_boundaries_separate_flag",
            "runtime_resolver_snapshot_identity_unchanged_flag",
            "upstream_report_references_immutable_flag",
            "upstream_receipt_references_immutable_flag",
        },
    },
    "owner_approval_receipt_boundary": {
        "type_field": "owner_approval_receipt_boundary_type",
        "type_value": OWNER_APPROVAL_RECEIPT_BOUNDARY_TYPE,
        "required": OWNER_APPROVAL_RECEIPT_BOUNDARY_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(OWNER_APPROVAL_RECEIPT_BOUNDARY_FIELDS),
        "true_fields": {"owner_approval_receipt_required_before_live_eligibility_flag"},
    },
    "gate_report": {
        "type_field": "report_type",
        "type_value": GATE_REPORT_TYPE,
        "required": REPORT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(REPORT_FIELDS),
        "true_fields": {"live_eligibility_requires_later_three_venue_canary_eligibility_gate"},
    },
    "handoff_block": {
        "type_field": "three_venue_canary_eligibility_handoff_block_type",
        "type_value": HANDOFF_BLOCK_TYPE,
        "required": HANDOFF_BLOCK_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(HANDOFF_BLOCK_FIELDS),
        "true_fields": {"live_eligibility_requires_later_three_venue_canary_eligibility_gate"},
    },
}

EXPECTED_STATE_BY_CASE = {
    "BLOCKED_MISSING_DUAL_RESULT_REVIEW_GATE_REPORT": (
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_GATE_REPORT_MISSING"
    ),
    "BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY": "BLOCKED_OWNER_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING",
    "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY": "BLOCKED_OWNER_REVIEW_PAPER_RESULT_BOUNDARY_MISSING",
    "BLOCKED_MISSING_DUAL_RESULT_REVIEW_INPUT_IDENTITY_DIGEST": (
        "BLOCKED_OWNER_REVIEW_INPUT_IDENTITY_DIGEST_MISSING"
    ),
    "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "BLOCKED_OWNER_REVIEW_RESULT_MERGE_CLAIM",
    "BLOCKED_STALE_DUAL_RESULT_REVIEW_REPORT": "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_STALE",
    "BLOCKED_SUPERSEDED_DUAL_RESULT_REVIEW_REPORT": (
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_SUPERSEDED"
    ),
    "BLOCKED_CONFLICT_STATE": "BLOCKED_OWNER_REVIEW_CONFLICT_STATE",
    "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_OWNER_REVIEW_SCHEMA_ERROR",
    "BLOCKED_LANE_MISMATCH": "BLOCKED_OWNER_REVIEW_LANE_MISMATCH",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_OWNER_REVIEW_TARGET_MISMATCH",
    "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM": (
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_DECISION_CLAIM"
    ),
    "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION_CLAIM": (
        "BLOCKED_OWNER_REVIEW_OWNER_APPROVAL_RECEIPT_CREATION_CLAIM"
    ),
    "BLOCKED_AUTO_LIVE_PROMOTION_CLAIM": "BLOCKED_OWNER_REVIEW_AUTO_LIVE_PROMOTION_CLAIM",
    "BLOCKED_DIRECT_CANARY_ELIGIBILITY_CLAIM": (
        "BLOCKED_OWNER_REVIEW_DIRECT_CANARY_ELIGIBILITY_CLAIM"
    ),
    "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM": (
        "BLOCKED_OWNER_REVIEW_DIRECT_CANARY_EXECUTION_CLAIM"
    ),
    "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": (
        "BLOCKED_OWNER_REVIEW_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM"
    ),
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": (
        "BLOCKED_OWNER_REVIEW_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM"
    ),
    "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKED_OWNER_REVIEW_BLOCKER_REDUCTION_CLAIM",
}

REQUIRED_FIXTURE_CASES = {
    "VALID_SYNTHETIC_STATIC_OWNER_LIVE_PROMOTION_REVIEW_INPUT_CONTRACT",
    "VALID_SYNTHETIC_BLOCKED_OWNER_APPROVAL_RECEIPT_BOUNDARY",
    "VALID_SYNTHETIC_THREE_VENUE_CANARY_ELIGIBILITY_HANDOFF_BLOCK",
    *EXPECTED_STATE_BY_CASE,
}

CLAIM_STATE_BY_TYPE = {
    "NONE": None,
    "RESULT_MERGE": "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM",
    "DUAL_RESULT_REVIEW_DECISION": "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM",
    "OWNER_APPROVAL_RECEIPT": "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION_CLAIM",
    "AUTO_LIVE_PROMOTION": "BLOCKED_AUTO_LIVE_PROMOTION_CLAIM",
    "DIRECT_CANARY_ELIGIBILITY": "BLOCKED_DIRECT_CANARY_ELIGIBILITY_CLAIM",
    "DIRECT_CANARY_EXECUTION": "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM",
    "LIVE_ORDER_RUNTIME_CASH_PROFIT": "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
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


def _walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _require_exact_fields(value: dict[str, Any], fields: Iterable[str], label: str) -> list[str]:
    return require_exact_fields(value, fields, label)


def _validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(value, label):
        if key in FORBIDDEN_TRUE_FIELDS and item is True:
            failures.append(f"{path} must remain false")
        if key in FORBIDDEN_COUNT_FIELDS and item not in {0, None}:
            failures.append(f"{path} must remain 0")
    return failures


def _validate_receipts(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{label} must be a non-empty list"]
    failures: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.startswith("SYNTHETIC_PR45_"):
            failures.append(f"{label} entries must be synthetic PR45 receipt ids")
    if len(set(value)) != len(value):
        failures.append(f"{label} must be unique")
    return failures


def _validate_blockers(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list"]
    if not value and not allow_empty:
        return [f"{label} must be a non-empty list"]
    failures: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.startswith("BLOCKED_"):
            failures.append(f"{label} entries must be blocked reason codes")
    if len(set(value)) != len(value):
        failures.append(f"{label} must be unique")
    return failures


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
    schema_path: pathlib.Path,
) -> list[str]:
    spec = SCHEMA_SPECS[schema_key]
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{schema_path}: schema root type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path}: schema must be closed at root")
    if _const(schema, spec["type_field"]) != spec["type_value"]:
        failures.append(f"{schema_path}: {spec['type_field']} const is invalid")

    missing_required = sorted(set(spec["required"]) - _required(schema))
    if missing_required:
        failures.append(f"{schema_path}: missing required schema fields: {', '.join(missing_required)}")
    unexpected_required = sorted(_required(schema) - set(spec["required"]))
    if unexpected_required:
        failures.append(f"{schema_path}: unexpected required schema fields: {', '.join(unexpected_required)}")

    for field in sorted(spec["false_fields"]):
        if _const(schema, field) is not False:
            failures.append(f"{schema_path}: {field} must have const false")
    for field in sorted(spec["true_fields"]):
        if _const(schema, field) is not True:
            failures.append(f"{schema_path}: {field} must have const true")
    return failures


def validate_input_contract_record(
    record: dict[str, Any],
    *,
    label: str = "owner live-promotion review input contract record",
) -> list[str]:
    failures = _require_exact_fields(record, INPUT_CONTRACT_FIELDS, label)
    if record.get("owner_live_promotion_review_input_contract_type") != INPUT_CONTRACT_TYPE:
        failures.append(f"{label}.owner_live_promotion_review_input_contract_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_OWNER_LIVE_PROMOTION_REVIEW_INPUT_CONTRACT_ONLY_NOT_OWNER_APPROVAL_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static input contract only")

    required_refs = [
        "dual_result_review_gate_report_ref",
        "replay_result_packet_boundary_ref",
        "paper_result_packet_boundary_ref",
        "dual_result_review_input_identity_digest",
    ]
    for field in required_refs:
        if not record.get(field):
            failures.append(f"{label}.{field} must be present")

    if record.get("replay_result_packet_boundary_ref") == record.get("paper_result_packet_boundary_ref"):
        failures.append(f"{label}.replay and paper result boundary refs must remain separate")
    if record.get("replay_result_packet_boundary_digest") == record.get("paper_result_packet_boundary_digest"):
        failures.append(f"{label}.replay and paper result boundary digests must remain separate")

    if record.get("dual_result_review_gate_report_state") != (
        "PRESENT_IMMUTABLE_PASS_OWNER_REVIEW_REQUIRED"
    ):
        failures.append(
            f"{label}.dual_result_review_gate_report_state must be "
            "PRESENT_IMMUTABLE_PASS_OWNER_REVIEW_REQUIRED"
        )
    if record.get("dual_result_review_state") != "PASS_OWNER_REVIEW_REQUIRED":
        failures.append(f"{label}.dual_result_review_state must be PASS_OWNER_REVIEW_REQUIRED")
    if record.get("input_identity_digest_state") != "PRESENT":
        failures.append(f"{label}.input_identity_digest_state must be PRESENT")
    if record.get("conflict_state") != "NO_CONFLICT":
        failures.append(f"{label}.conflict_state must be NO_CONFLICT")
    if record.get("schema_state") != "SCHEMA_VALID":
        failures.append(f"{label}.schema_state must be SCHEMA_VALID")
    if record.get("lane_match_state") != "MATCH":
        failures.append(f"{label}.lane_match_state must be MATCH")
    if record.get("target_match_state") != "MATCH":
        failures.append(f"{label}.target_match_state must be MATCH")
    if record.get("dual_result_review_pass_next_allowed_consumer") != OWNER_REVIEW_ONLY_CONSUMER:
        failures.append(f"{label}.dual_result_review_pass_next_allowed_consumer must be {OWNER_REVIEW_ONLY_CONSUMER}")
    if record.get("owner_live_promotion_review_pass_next_allowed_consumer") != (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    ):
        failures.append(
            f"{label}.owner_live_promotion_review_pass_next_allowed_consumer must be "
            f"{THREE_VENUE_CANARY_GATE_ONLY_CONSUMER}"
        )

    runtime_id = record.get("runtime_resolver_snapshot_id")
    for field in [
        "dual_result_runtime_resolver_snapshot_id",
        "replay_runtime_resolver_snapshot_id",
        "paper_runtime_resolver_snapshot_id",
    ]:
        if record.get(field) != runtime_id:
            failures.append(f"{label}.{field} must match runtime_resolver_snapshot_id")
    runtime_digest = record.get("runtime_resolver_snapshot_digest")
    for field in [
        "dual_result_runtime_resolver_snapshot_digest",
        "replay_runtime_resolver_snapshot_digest",
        "paper_runtime_resolver_snapshot_digest",
    ]:
        if record.get(field) != runtime_digest:
            failures.append(f"{label}.{field} must match runtime_resolver_snapshot_digest")

    for field in [
        "live_eligibility_requires_later_three_venue_canary_eligibility_gate",
        "owner_review_required_after_dual_result_review_flag",
        "replay_paper_result_boundaries_separate_flag",
        "runtime_resolver_snapshot_identity_unchanged_flag",
        "upstream_report_references_immutable_flag",
        "upstream_receipt_references_immutable_flag",
    ]:
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", allow_empty=True))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_owner_approval_receipt_boundary_record(
    record: dict[str, Any],
    *,
    label: str = "owner approval receipt boundary record",
) -> list[str]:
    failures = _require_exact_fields(record, OWNER_APPROVAL_RECEIPT_BOUNDARY_FIELDS, label)
    if record.get("owner_approval_receipt_boundary_type") != OWNER_APPROVAL_RECEIPT_BOUNDARY_TYPE:
        failures.append(f"{label}.owner_approval_receipt_boundary_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_OWNER_APPROVAL_RECEIPT_BOUNDARY_ONLY_NOT_OWNER_APPROVAL_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static receipt boundary only")
    if record.get("owner_approval_receipt_creation_authority_state") != "BLOCKED_STATIC_CONTRACT_ONLY":
        failures.append(
            f"{label}.owner_approval_receipt_creation_authority_state must be "
            "BLOCKED_STATIC_CONTRACT_ONLY"
        )
    if record.get("owner_approval_receipt_required_before_live_eligibility_flag") is not True:
        failures.append(f"{label}.owner_approval_receipt_required_before_live_eligibility_flag must be true")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(OWNER_APPROVAL_RECEIPT_BOUNDARY_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_handoff_block_record(
    record: dict[str, Any],
    *,
    label: str = "three-venue canary eligibility handoff block record",
) -> list[str]:
    failures = _require_exact_fields(record, HANDOFF_BLOCK_FIELDS, label)
    if record.get("three_venue_canary_eligibility_handoff_block_type") != HANDOFF_BLOCK_TYPE:
        failures.append(f"{label}.three_venue_canary_eligibility_handoff_block_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_THREE_VENUE_CANARY_ELIGIBILITY_HANDOFF_BLOCK_ONLY_NOT_CANARY_ELIGIBILITY_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static handoff only")
    if record.get("dual_result_review_pass_next_allowed_consumer") != OWNER_REVIEW_ONLY_CONSUMER:
        failures.append(f"{label}.dual_result_review_pass_next_allowed_consumer must be {OWNER_REVIEW_ONLY_CONSUMER}")
    if record.get("owner_live_promotion_review_pass_next_allowed_consumer") != (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    ):
        failures.append(
            f"{label}.owner_live_promotion_review_pass_next_allowed_consumer must be "
            f"{THREE_VENUE_CANARY_GATE_ONLY_CONSUMER}"
        )
    if record.get("handoff_block_scope") != "STATIC_HANDOFF_ONLY_NOT_THREE_VENUE_CANARY_ELIGIBILITY_GATE":
        failures.append(f"{label}.handoff_block_scope must be static handoff only")
    if record.get("live_eligibility_requires_later_three_venue_canary_eligibility_gate") is not True:
        failures.append(
            f"{label}.live_eligibility_requires_later_three_venue_canary_eligibility_gate must be true"
        )
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(HANDOFF_BLOCK_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_gate_case_record(
    record: dict[str, Any],
    *,
    label: str = "owner live-promotion review gate case record",
) -> list[str]:
    failures = _require_exact_fields(record, CASE_FIELDS, label)
    if record.get("case_record_type") != "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_GATE_CASE":
        failures.append(f"{label}.case_record_type is invalid")
    if record.get("case_authority_class") != "SYNTHETIC_CASE_ONLY_NOT_OWNER_LIVE_PROMOTION_REVIEW_AUTHORITY":
        failures.append(f"{label}.case_authority_class must be synthetic case only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")

    case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR45 case")
    elif record.get("expected_gate_state") != expected_state:
        failures.append(f"{label}.expected_gate_state must be {expected_state}")

    state_expectations = {
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_GATE_REPORT_MISSING": (
            record.get("dual_result_review_gate_report_state") == "MISSING"
        ),
        "BLOCKED_OWNER_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING": (
            record.get("replay_result_boundary_reference_state") == "MISSING"
        ),
        "BLOCKED_OWNER_REVIEW_PAPER_RESULT_BOUNDARY_MISSING": (
            record.get("paper_result_boundary_reference_state") == "MISSING"
        ),
        "BLOCKED_OWNER_REVIEW_INPUT_IDENTITY_DIGEST_MISSING": (
            record.get("input_identity_digest_state") == "MISSING"
        ),
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_STALE": (
            record.get("dual_result_review_gate_report_state") == "STALE"
        ),
        "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_SUPERSEDED": (
            record.get("dual_result_review_gate_report_state") == "SUPERSEDED"
        ),
        "BLOCKED_OWNER_REVIEW_CONFLICT_STATE": record.get("conflict_state") == "CONFLICT_PRESENT",
        "BLOCKED_OWNER_REVIEW_SCHEMA_ERROR": record.get("schema_state") == "SCHEMA_ERROR",
        "BLOCKED_OWNER_REVIEW_LANE_MISMATCH": record.get("lane_match_state") == "MISMATCH",
        "BLOCKED_OWNER_REVIEW_TARGET_MISMATCH": record.get("target_match_state") == "MISMATCH",
    }
    if expected_state in state_expectations and not state_expectations[expected_state]:
        failures.append(f"{label}.{case} state fields do not match expected blocked state")

    claim_type = record.get("claim_attempt_type")
    if claim_type not in CLAIM_STATE_BY_TYPE:
        failures.append(f"{label}.claim_attempt_type is invalid")
    else:
        claim_case = CLAIM_STATE_BY_TYPE[claim_type]
        if claim_case is None:
            if isinstance(case, str) and case.endswith("_CLAIM"):
                failures.append(f"{label}.claim_attempt_type must explain blocked claim case")
        elif case != claim_case:
            failures.append(f"{label}.claim_attempt_type does not match fixture_case")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_no_forbidden_claims(record, label))
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = _require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_OWNER_APPROVAL_NOT_SOURCE_FACT"
    ):
        failures.append("fixture.fixture_authority_class must be synthetic owner-review non-authority")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_DUAL_RESULT_REVIEW_NOT_OWNER_APPROVAL_NOT_CANARY_ELIGIBILITY"
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
        "owner_live_promotion_review_input_contract_records": fixture.get(
            "owner_live_promotion_review_input_contract_records"
        ),
        "owner_approval_receipt_boundary_records": fixture.get("owner_approval_receipt_boundary_records"),
        "three_venue_canary_eligibility_handoff_block_records": fixture.get(
            "three_venue_canary_eligibility_handoff_block_records"
        ),
        "owner_live_promotion_review_gate_case_records": fixture.get(
            "owner_live_promotion_review_gate_case_records"
        ),
    }
    for name, records in groups.items():
        if not isinstance(records, list) or not records:
            failures.append(f"fixture.{name} must be a non-empty list")
            groups[name] = []

    seen_cases: set[str] = set()
    for index, record in enumerate(groups["owner_live_promotion_review_input_contract_records"]):
        if not isinstance(record, dict):
            failures.append(f"owner_live_promotion_review_input_contract_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_input_contract_record(
                record,
                label=f"owner_live_promotion_review_input_contract_records[{index}]",
            )
        )

    for index, record in enumerate(groups["owner_approval_receipt_boundary_records"]):
        if not isinstance(record, dict):
            failures.append(f"owner_approval_receipt_boundary_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_owner_approval_receipt_boundary_record(
                record,
                label=f"owner_approval_receipt_boundary_records[{index}]",
            )
        )

    for index, record in enumerate(groups["three_venue_canary_eligibility_handoff_block_records"]):
        if not isinstance(record, dict):
            failures.append(f"three_venue_canary_eligibility_handoff_block_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_handoff_block_record(
                record,
                label=f"three_venue_canary_eligibility_handoff_block_records[{index}]",
            )
        )

    for index, record in enumerate(groups["owner_live_promotion_review_gate_case_records"]):
        if not isinstance(record, dict):
            failures.append(f"owner_live_promotion_review_gate_case_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_gate_case_record(record, label=f"owner_live_promotion_review_gate_case_records[{index}]"))

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - seen_cases)
    if missing_cases:
        failures.append(f"fixture missing required PR45 cases: {', '.join(missing_cases)}")
    failures.extend(validate_current_atomicrows_bundle_state(repo_root, label="PR45 owner live-promotion review fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    input_contract_schema_path: pathlib.Path = DEFAULT_INPUT_CONTRACT_SCHEMA,
    owner_approval_receipt_boundary_schema_path: pathlib.Path = DEFAULT_OWNER_APPROVAL_RECEIPT_BOUNDARY_SCHEMA,
    gate_report_schema_path: pathlib.Path = DEFAULT_GATE_REPORT_SCHEMA,
    handoff_block_schema_path: pathlib.Path = DEFAULT_HANDOFF_BLOCK_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schema_paths = {
        "input_contract": input_contract_schema_path,
        "owner_approval_receipt_boundary": owner_approval_receipt_boundary_schema_path,
        "gate_report": gate_report_schema_path,
        "handoff_block": handoff_block_schema_path,
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
    failures.extend(validate_current_atomicrows_bundle_state(repo_root, label="PR45 owner live-promotion review validator"))
    return failures


def _case_counts(cases: Sequence[Any]) -> dict[str, int]:
    counts = {
        "blocked_missing_dual_result_review_gate_case_count": 0,
        "blocked_missing_replay_or_paper_boundary_case_count": 0,
        "blocked_missing_digest_case_count": 0,
        "blocked_stale_conflict_schema_lane_target_case_count": 0,
        "blocked_result_merge_or_decision_case_count": 0,
        "blocked_owner_approval_or_auto_promotion_case_count": 0,
        "blocked_canary_shortcut_case_count": 0,
        "blocked_live_cash_profit_atomicrows_case_count": 0,
        "blocked_blocker_reduction_case_count": 0,
    }
    for record in cases:
        if not isinstance(record, dict):
            continue
        case = record.get("fixture_case")
        if case == "BLOCKED_MISSING_DUAL_RESULT_REVIEW_GATE_REPORT":
            counts["blocked_missing_dual_result_review_gate_case_count"] += 1
        if case in {"BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY", "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY"}:
            counts["blocked_missing_replay_or_paper_boundary_case_count"] += 1
        if case == "BLOCKED_MISSING_DUAL_RESULT_REVIEW_INPUT_IDENTITY_DIGEST":
            counts["blocked_missing_digest_case_count"] += 1
        if case in {
            "BLOCKED_STALE_DUAL_RESULT_REVIEW_REPORT",
            "BLOCKED_SUPERSEDED_DUAL_RESULT_REVIEW_REPORT",
            "BLOCKED_CONFLICT_STATE",
            "BLOCKED_SCHEMA_ERROR_STATE",
            "BLOCKED_LANE_MISMATCH",
            "BLOCKED_TARGET_MISMATCH",
        }:
            counts["blocked_stale_conflict_schema_lane_target_case_count"] += 1
        if case in {"BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM", "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM"}:
            counts["blocked_result_merge_or_decision_case_count"] += 1
        if case in {
            "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION_CLAIM",
            "BLOCKED_AUTO_LIVE_PROMOTION_CLAIM",
        }:
            counts["blocked_owner_approval_or_auto_promotion_case_count"] += 1
        if case in {
            "BLOCKED_DIRECT_CANARY_ELIGIBILITY_CLAIM",
            "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM",
        }:
            counts["blocked_canary_shortcut_case_count"] += 1
        if case in {
            "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
            "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
        }:
            counts["blocked_live_cash_profit_atomicrows_case_count"] += 1
        if case == "BLOCKED_BLOCKER_REDUCTION_CLAIM":
            counts["blocked_blocker_reduction_case_count"] += 1
    return counts


def _all_fixture_records(fixture: dict[str, Any] | None) -> list[Any]:
    if fixture is None:
        return []
    records: list[Any] = []
    for key in [
        "owner_live_promotion_review_input_contract_records",
        "owner_approval_receipt_boundary_records",
        "three_venue_canary_eligibility_handoff_block_records",
        "owner_live_promotion_review_gate_case_records",
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
    inputs = fixture.get("owner_live_promotion_review_input_contract_records", []) if fixture else []
    receipt_boundaries = fixture.get("owner_approval_receipt_boundary_records", []) if fixture else []
    handoffs = fixture.get("three_venue_canary_eligibility_handoff_block_records", []) if fixture else []
    cases = fixture.get("owner_live_promotion_review_gate_case_records", []) if fixture else []
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
        "report_version": "PR45_STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_REPORT_V1",
        "master_plan_edition": "v9.9.745",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "input_contract_record_count": len(inputs),
        "owner_approval_receipt_boundary_record_count": len(receipt_boundaries),
        "three_venue_canary_handoff_block_record_count": len(handoffs),
        "gate_case_record_count": len(cases),
        **_case_counts(cases),
        "gate_state": "FAIL" if validation_failures else STATIC_GATE_STATE,
        "validation_failure_count": len(validation_failures),
        "dual_result_review_pass_next_allowed_consumer": OWNER_REVIEW_ONLY_CONSUMER,
        "owner_live_promotion_review_pass_next_allowed_consumer": THREE_VENUE_CANARY_GATE_ONLY_CONSUMER,
        "owner_live_promotion_review_direct_live_consumer_allowed": False,
        "owner_live_promotion_review_direct_order_router_allowed": False,
        "owner_live_promotion_review_direct_canary_execution_allowed": False,
        "owner_live_promotion_review_auto_approval_allowed": False,
        "owner_live_promotion_review_auto_promotion_allowed": False,
        "live_eligibility_requires_later_three_venue_canary_eligibility_gate": True,
        "owner_live_promotion_review_decision_created_flag": False,
        "owner_approval_receipt_created_flag": False,
        "live_eligibility_allowed_flag": False,
        "three_venue_canary_eligibility_allowed_flag": False,
        "three_venue_canary_eligibility_created_flag": False,
        "limited_live_canary_execution_created_flag": False,
        "live_reachability_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "runtime_cash_claim_allowed_flag": False,
        "atomicrows_bundle_hash_created_or_mutated_flag": False,
        "blocker_reduction_claim_created_flag": False,
        "profit_claim_allowed_flag": False,
        "blocker_codes": blocker_codes,
        "receipt_ids_emitted": receipt_ids,
        "no_claim_flags": dict(NO_CLAIM_FLAGS),
        "validation_hook_ids": [VALIDATION_HOOK],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-contract-schema", default=str(DEFAULT_INPUT_CONTRACT_SCHEMA))
    parser.add_argument(
        "--owner-approval-receipt-boundary-schema",
        default=str(DEFAULT_OWNER_APPROVAL_RECEIPT_BOUNDARY_SCHEMA),
    )
    parser.add_argument("--gate-report-schema", default=str(DEFAULT_GATE_REPORT_SCHEMA))
    parser.add_argument("--handoff-block-schema", default=str(DEFAULT_HANDOFF_BLOCK_SCHEMA))
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
        owner_approval_receipt_boundary_schema_path=pathlib.Path(
            args.owner_approval_receipt_boundary_schema
        ),
        gate_report_schema_path=pathlib.Path(args.gate_report_schema),
        handoff_block_schema_path=pathlib.Path(args.handoff_block_schema),
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
