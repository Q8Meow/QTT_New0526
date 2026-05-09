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
    canonical_atomicrows_absence_failures,
    load_json_object,
    require_bool_map,
    require_exact_fields,
    write_json,
)

SUCCESS_MARKER = "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_OK"
FAILURE_MARKER = "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_STATIC_AUDIT"

INPUT_CONTRACT_TYPE = "STAGE1_DUAL_RESULT_REVIEW_INPUT_CONTRACT"
COMPARISON_MATRIX_TYPE = "STAGE1_REPLAY_PAPER_COMPARISON_MATRIX"
GATE_REPORT_TYPE = "STAGE1_DUAL_RESULT_REVIEW_GATE_REPORT"
HANDOFF_BLOCK_TYPE = "STAGE1_OWNER_LIVE_PROMOTION_HANDOFF_BLOCK"

EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
STATIC_GATE_STATE = "STATIC_DUAL_RESULT_REVIEW_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
OWNER_REVIEW_ONLY_CONSUMER = "OWNER_LIVE_PROMOTION_REVIEW_ONLY"

DEFAULT_INPUT_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_dual_result_review_input_contract.schema.json"
)
DEFAULT_COMPARISON_MATRIX_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_replay_paper_comparison_matrix.schema.json"
)
DEFAULT_GATE_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_dual_result_review_gate_report.schema.json"
)
DEFAULT_HANDOFF_BLOCK_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_owner_live_promotion_handoff_block.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/dual_result_review/"
    "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
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
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FALSE_BOUNDARY_FIELDS = {
    "auto_promotion_allowed_flag",
    "direct_live_promotion_claimed_flag",
    "dual_result_review_auto_promotion_allowed",
    "dual_result_review_decision_created_flag",
    "dual_result_review_direct_canary_allowed",
    "dual_result_review_direct_live_consumer_allowed",
    "dual_result_review_direct_order_router_allowed",
    "live_eligibility_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_live_promotion_review_created_flag",
    "owner_promotion_readiness_created_flag",
    "paper_result_packet_mutated_flag",
    "profit_claim_created_flag",
    "profit_evidence_created_flag",
    "replay_paper_results_merged_flag",
    "replay_result_packet_mutated_flag",
    "result_merge_created_flag",
    "runtime_cash_claim_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "combined_result_packet_created_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | FALSE_BOUNDARY_FIELDS | {
    "accepted_source_fact_created",
    "atomicrows_bundle_created",
    "atomicrows_hash_created",
    "auto_promotion_created",
    "blocker_reduction_claimed",
    "dual_result_review_decision_created",
    "live_order_authority_created",
    "owner_approval_receipt_created",
    "owner_live_promotion_review_created",
    "replay_paper_result_merge_created",
}

FORBIDDEN_COUNT_FIELDS = {
    "accepted_source_fact_created_count",
    "auto_promotion_claim_count",
    "blocker_reduction_claim_count",
    "dual_result_review_decision_created_count",
    "live_order_runtime_cash_profit_claim_count",
    "owner_approval_receipt_created_count",
    "owner_live_promotion_review_created_count",
    "replay_paper_result_merge_claim_count",
    "atomicrows_bundle_hash_mutation_claim_count",
}

INPUT_CONTRACT_FIELDS = {
    "dual_result_review_input_contract_type",
    "dual_result_review_input_contract_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "concurrent_replay_paper_execution_gate_report_ref",
    "replay_result_packet_boundary_ref",
    "paper_result_packet_boundary_ref",
    "replay_result_packet_boundary_digest",
    "paper_result_packet_boundary_digest",
    "replay_paper_input_identity_digest",
    "replay_lane_replay_paper_input_identity_digest",
    "paper_lane_replay_paper_input_identity_digest",
    "runtime_resolver_snapshot_id",
    "replay_runtime_resolver_snapshot_id",
    "paper_runtime_resolver_snapshot_id",
    "runtime_resolver_snapshot_digest",
    "replay_runtime_resolver_snapshot_digest",
    "paper_runtime_resolver_snapshot_digest",
    "replay_result_boundary_state",
    "paper_result_boundary_state",
    "input_identity_match_state",
    "runtime_resolver_snapshot_match_state",
    "digest_presence_state",
    "conflict_state",
    "schema_state",
    "lane_match_state",
    "target_match_state",
    "replay_result_reference_immutable_flag",
    "paper_result_reference_immutable_flag",
    "review_decision_created_flag",
    "ready_for_comparison_matrix_flag",
    "result_merge_created_flag",
    "auto_promotion_allowed_flag",
    "owner_live_promotion_review_created_flag",
    "owner_approval_receipt_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "runtime_cash_claim_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_evidence_created_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

MATRIX_PAIR_FIELDS = {
    "metric_pair_id",
    "replay_metric_ref",
    "paper_metric_ref",
    "metric_merge_allowed_flag",
    "metric_average_for_promotion_allowed_flag",
    "negative_lane_metric_drop_allowed_flag",
    "static_comparison_only_flag",
}

COMPARISON_MATRIX_FIELDS = {
    "comparison_matrix_type",
    "comparison_matrix_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "input_contract_ref",
    "replay_result_packet_boundary_ref",
    "paper_result_packet_boundary_ref",
    "static_fields_only_flag",
    "compares_synthetic_boundary_refs_only_flag",
    "metric_pair_records",
    "comparison_summary_state",
    "next_required_state",
    "negative_lane_metrics_preserved_flag",
    "replay_result_packet_mutated_flag",
    "paper_result_packet_mutated_flag",
    "replay_paper_results_merged_flag",
    "combined_result_packet_created_flag",
    "dual_result_review_decision_created_flag",
    "live_eligibility_created_flag",
    "owner_promotion_readiness_created_flag",
    "owner_live_promotion_review_created_flag",
    "owner_approval_receipt_created_flag",
    "direct_live_promotion_claimed_flag",
    "order_authority_created_flag",
    "runtime_cash_claim_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_claim_created_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

HANDOFF_BLOCK_FIELDS = {
    "handoff_block_type",
    "handoff_block_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "dual_result_review_pass_next_allowed_consumer",
    "dual_result_review_direct_live_consumer_allowed",
    "dual_result_review_direct_order_router_allowed",
    "dual_result_review_direct_canary_allowed",
    "dual_result_review_auto_promotion_allowed",
    "owner_review_required_before_live_eligibility",
    "owner_live_promotion_review_created_flag",
    "owner_approval_receipt_created_flag",
    "live_eligibility_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "runtime_cash_claim_created_flag",
    "profit_claim_created_flag",
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
    "replay_result_boundary_reference_state",
    "paper_result_boundary_reference_state",
    "input_identity_digest_state",
    "input_identity_digest_match_state",
    "runtime_resolver_snapshot_id_match_state",
    "runtime_resolver_snapshot_digest_match_state",
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
    "dual_result_review_input_contract_records",
    "replay_paper_comparison_matrix_records",
    "owner_live_promotion_handoff_block_records",
    "dual_result_review_gate_case_records",
}

REPORT_FIELDS = {
    "report_type",
    "report_version",
    "master_plan_edition",
    "master_plan_sha256",
    "created_at_utc",
    "input_contract_record_count",
    "comparison_matrix_record_count",
    "handoff_block_record_count",
    "gate_case_record_count",
    "blocked_missing_result_boundary_case_count",
    "blocked_identity_or_snapshot_mismatch_case_count",
    "blocked_stale_conflict_schema_target_case_count",
    "blocked_merge_or_decision_case_count",
    "blocked_auto_promotion_or_owner_review_case_count",
    "blocked_live_cash_profit_atomicrows_case_count",
    "gate_state",
    "validation_failure_count",
    "dual_result_review_pass_next_allowed_consumer",
    "dual_result_review_direct_live_consumer_allowed",
    "dual_result_review_direct_order_router_allowed",
    "dual_result_review_direct_canary_allowed",
    "dual_result_review_auto_promotion_allowed",
    "owner_review_required_before_live_eligibility",
    "replay_result_packet_created_flag",
    "paper_result_packet_created_flag",
    "replay_paper_results_merged_flag",
    "dual_result_review_decision_created_flag",
    "owner_live_promotion_review_created_flag",
    "owner_approval_receipt_created_flag",
    "live_eligibility_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "runtime_cash_claim_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_evidence_created_flag",
    "blocker_codes",
    "receipt_ids_emitted",
    "no_claim_flags",
    "validation_hook_ids",
}

SCHEMA_SPECS = {
    "input_contract": {
        "type_field": "dual_result_review_input_contract_type",
        "type_value": INPUT_CONTRACT_TYPE,
        "required": INPUT_CONTRACT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS)
        | {"review_decision_created_flag"},
        "true_fields": {
            "replay_result_reference_immutable_flag",
            "paper_result_reference_immutable_flag",
            "ready_for_comparison_matrix_flag",
        },
    },
    "comparison_matrix": {
        "type_field": "comparison_matrix_type",
        "type_value": COMPARISON_MATRIX_TYPE,
        "required": COMPARISON_MATRIX_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(COMPARISON_MATRIX_FIELDS),
        "true_fields": {
            "static_fields_only_flag",
            "compares_synthetic_boundary_refs_only_flag",
            "negative_lane_metrics_preserved_flag",
        },
    },
    "gate_report": {
        "type_field": "report_type",
        "type_value": GATE_REPORT_TYPE,
        "required": REPORT_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(REPORT_FIELDS)
        | {
            "replay_result_packet_created_flag",
            "paper_result_packet_created_flag",
            "dual_result_review_direct_live_consumer_allowed",
            "dual_result_review_direct_order_router_allowed",
            "dual_result_review_direct_canary_allowed",
            "dual_result_review_auto_promotion_allowed",
        },
        "true_fields": {"owner_review_required_before_live_eligibility"},
    },
    "handoff_block": {
        "type_field": "handoff_block_type",
        "type_value": HANDOFF_BLOCK_TYPE,
        "required": HANDOFF_BLOCK_FIELDS,
        "false_fields": FALSE_BOUNDARY_FIELDS.intersection(HANDOFF_BLOCK_FIELDS),
        "true_fields": {"owner_review_required_before_live_eligibility"},
    },
}

EXPECTED_STATE_BY_CASE = {
    "BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING",
    "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_PAPER_RESULT_BOUNDARY_MISSING",
    "BLOCKED_MISSING_INPUT_IDENTITY_DIGEST": "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_DIGEST_MISSING",
    "BLOCKED_MISMATCHED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST": "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_MISMATCH",
    "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_ID": "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_ID_MISMATCH",
    "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST": "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISMATCH",
    "BLOCKED_STALE_REPLAY_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_STALE_REPLAY_RESULT_BOUNDARY",
    "BLOCKED_STALE_PAPER_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_STALE_PAPER_RESULT_BOUNDARY",
    "BLOCKED_CONFLICT_STATE": "BLOCKED_DUAL_REVIEW_CONFLICT_STATE",
    "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_DUAL_REVIEW_SCHEMA_ERROR",
    "BLOCKED_LANE_MISMATCH": "BLOCKED_DUAL_REVIEW_LANE_MISMATCH",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_DUAL_REVIEW_TARGET_MISMATCH",
    "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "BLOCKED_DUAL_REVIEW_RESULT_MERGE_OR_OVERWRITE_DETECTED",
    "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM": "BLOCKED_DUAL_REVIEW_DECISION_CREATION_CLAIM",
    "BLOCKED_AUTO_PROMOTION_CLAIM": "BLOCKED_DUAL_REVIEW_AUTO_PROMOTION_ATTEMPT",
    "BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_CREATION": "BLOCKED_DUAL_REVIEW_OWNER_LIVE_PROMOTION_REVIEW_CREATED",
    "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION": "BLOCKED_DUAL_REVIEW_OWNER_APPROVAL_RECEIPT_CREATED",
    "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "BLOCKED_DUAL_REVIEW_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "BLOCKED_DUAL_REVIEW_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKED_DUAL_REVIEW_BLOCKER_REDUCTION_CLAIM",
}

REQUIRED_FIXTURE_CASES = {
    "VALID_SYNTHETIC_STATIC_DUAL_RESULT_REVIEW_INPUT_CONTRACT",
    "VALID_SYNTHETIC_BLOCKED_COMPARISON_MATRIX",
    "VALID_SYNTHETIC_OWNER_LIVE_PROMOTION_HANDOFF_BLOCK",
    *EXPECTED_STATE_BY_CASE,
}

CLAIM_STATE_BY_TYPE = {
    "NONE": None,
    "REPLAY_PAPER_RESULT_MERGE": "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM",
    "DUAL_RESULT_REVIEW_DECISION": "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM",
    "AUTO_PROMOTION": "BLOCKED_AUTO_PROMOTION_CLAIM",
    "OWNER_LIVE_PROMOTION_REVIEW_CREATION": "BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_CREATION",
    "OWNER_APPROVAL_RECEIPT": "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION",
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
        if not isinstance(item, str) or not item.startswith("SYNTHETIC_PR44_"):
            failures.append(f"{label} entries must be synthetic PR44 receipt ids")
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
    failures: list[str] = []
    spec = SCHEMA_SPECS[schema_key]
    props = _properties(schema)
    required = _required(schema)

    if schema.get("type") != "object":
        failures.append(f"{schema_path}: schema root type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path}: additionalProperties must be false")
    missing_properties = sorted(spec["required"] - set(props))
    missing_required = sorted(spec["required"] - required)
    if missing_properties:
        failures.append(f"{schema_path}: missing properties: {', '.join(missing_properties)}")
    if missing_required:
        failures.append(f"{schema_path}: missing required fields: {', '.join(missing_required)}")
    if _const(schema, spec["type_field"]) != spec["type_value"]:
        failures.append(f"{schema_path}: {spec['type_field']} const is invalid")
    for field in sorted(spec["false_fields"]):
        if field in props and _const(schema, field) is not False:
            failures.append(f"{schema_path}: {field} must be const false")
    for field in sorted(spec["true_fields"]):
        if field in props and _const(schema, field) is not True:
            failures.append(f"{schema_path}: {field} must be const true")

    no_claim_ref = props.get("no_claim_flags", {})
    if isinstance(no_claim_ref, dict) and no_claim_ref.get("$ref") != "#/$defs/no_claim_flags":
        failures.append(f"{schema_path}: no_claim_flags must use local no_claim_flags definition")
    return failures


def validate_input_contract_record(
    record: dict[str, Any],
    *,
    label: str = "input contract record",
) -> list[str]:
    failures = _require_exact_fields(record, INPUT_CONTRACT_FIELDS, label)
    if record.get("dual_result_review_input_contract_type") != INPUT_CONTRACT_TYPE:
        failures.append(f"{label}.dual_result_review_input_contract_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_DUAL_RESULT_REVIEW_INPUT_CONTRACT_ONLY_NOT_REVIEW_DECISION_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static input contract only")

    for field in [
        "concurrent_replay_paper_execution_gate_report_ref",
        "replay_result_packet_boundary_ref",
        "paper_result_packet_boundary_ref",
        "replay_paper_input_identity_digest",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
    ]:
        if not record.get(field):
            failures.append(f"{label}.{field} must be present")

    if record.get("replay_result_packet_boundary_ref") == record.get("paper_result_packet_boundary_ref"):
        failures.append(f"{label} replay and paper boundary refs must remain separate")
    if record.get("replay_paper_input_identity_digest") != record.get(
        "replay_lane_replay_paper_input_identity_digest"
    ):
        failures.append(f"{label}.replay lane input identity digest must match")
    if record.get("replay_paper_input_identity_digest") != record.get(
        "paper_lane_replay_paper_input_identity_digest"
    ):
        failures.append(f"{label}.paper lane input identity digest must match")
    if record.get("runtime_resolver_snapshot_id") != record.get("replay_runtime_resolver_snapshot_id"):
        failures.append(f"{label}.replay runtime resolver snapshot id must match")
    if record.get("runtime_resolver_snapshot_id") != record.get("paper_runtime_resolver_snapshot_id"):
        failures.append(f"{label}.paper runtime resolver snapshot id must match")
    if record.get("runtime_resolver_snapshot_digest") != record.get(
        "replay_runtime_resolver_snapshot_digest"
    ):
        failures.append(f"{label}.replay runtime resolver snapshot digest must match")
    if record.get("runtime_resolver_snapshot_digest") != record.get(
        "paper_runtime_resolver_snapshot_digest"
    ):
        failures.append(f"{label}.paper runtime resolver snapshot digest must match")

    expected_states = {
        "replay_result_boundary_state": "PRESENT_IMMUTABLE",
        "paper_result_boundary_state": "PRESENT_IMMUTABLE",
        "input_identity_match_state": "MATCH",
        "runtime_resolver_snapshot_match_state": "MATCH",
        "digest_presence_state": "PRESENT",
        "conflict_state": "NO_CONFLICT",
        "schema_state": "SCHEMA_VALID",
        "lane_match_state": "MATCH",
        "target_match_state": "MATCH",
    }
    for field, expected in expected_states.items():
        if record.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")

    for field in ["replay_result_reference_immutable_flag", "paper_result_reference_immutable_flag", "ready_for_comparison_matrix_flag"]:
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(INPUT_CONTRACT_FIELDS) | {"review_decision_created_flag"}):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", allow_empty=True))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_comparison_matrix_record(
    record: dict[str, Any],
    *,
    label: str = "comparison matrix record",
) -> list[str]:
    failures = _require_exact_fields(record, COMPARISON_MATRIX_FIELDS, label)
    if record.get("comparison_matrix_type") != COMPARISON_MATRIX_TYPE:
        failures.append(f"{label}.comparison_matrix_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_REPLAY_PAPER_COMPARISON_MATRIX_ONLY_NOT_RESULT_MERGE_NOT_PROMOTION_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static comparison only")
    if record.get("replay_result_packet_boundary_ref") == record.get("paper_result_packet_boundary_ref"):
        failures.append(f"{label} replay and paper boundary refs must remain separate")
    for field in [
        "static_fields_only_flag",
        "compares_synthetic_boundary_refs_only_flag",
        "negative_lane_metrics_preserved_flag",
    ]:
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in sorted(FALSE_BOUNDARY_FIELDS.intersection(COMPARISON_MATRIX_FIELDS)):
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if record.get("next_required_state") != "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED":
        failures.append(f"{label}.next_required_state must require owner review")

    pairs = record.get("metric_pair_records")
    if not isinstance(pairs, list) or not pairs:
        failures.append(f"{label}.metric_pair_records must be a non-empty list")
    else:
        for index, pair in enumerate(pairs):
            pair_label = f"{label}.metric_pair_records[{index}]"
            if not isinstance(pair, dict):
                failures.append(f"{pair_label} must be an object")
                continue
            failures.extend(_require_exact_fields(pair, MATRIX_PAIR_FIELDS, pair_label))
            for field in [
                "metric_merge_allowed_flag",
                "metric_average_for_promotion_allowed_flag",
                "negative_lane_metric_drop_allowed_flag",
            ]:
                if pair.get(field) is not False:
                    failures.append(f"{pair_label}.{field} must be false")
            if pair.get("static_comparison_only_flag") is not True:
                failures.append(f"{pair_label}.static_comparison_only_flag must be true")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes"))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_handoff_block_record(
    record: dict[str, Any],
    *,
    label: str = "handoff block record",
) -> list[str]:
    failures = _require_exact_fields(record, HANDOFF_BLOCK_FIELDS, label)
    if record.get("handoff_block_type") != HANDOFF_BLOCK_TYPE:
        failures.append(f"{label}.handoff_block_type is invalid")
    if record.get("record_authority_class") != (
        "STATIC_OWNER_LIVE_PROMOTION_HANDOFF_BLOCK_ONLY_NOT_OWNER_REVIEW_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static handoff block only")
    if record.get("dual_result_review_pass_next_allowed_consumer") != OWNER_REVIEW_ONLY_CONSUMER:
        failures.append(f"{label}.dual_result_review_pass_next_allowed_consumer must be {OWNER_REVIEW_ONLY_CONSUMER}")
    if record.get("owner_review_required_before_live_eligibility") is not True:
        failures.append(f"{label}.owner_review_required_before_live_eligibility must be true")
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
    label: str = "gate case record",
) -> list[str]:
    failures = _require_exact_fields(record, CASE_FIELDS, label)
    if record.get("case_record_type") != "STAGE1_DUAL_RESULT_REVIEW_GATE_CASE":
        failures.append(f"{label}.case_record_type is invalid")
    if record.get("case_authority_class") != "SYNTHETIC_CASE_ONLY_NOT_DUAL_RESULT_REVIEW_AUTHORITY":
        failures.append(f"{label}.case_authority_class must be synthetic case only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")

    case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR44 case")
    elif record.get("expected_gate_state") != expected_state:
        failures.append(f"{label}.expected_gate_state must be {expected_state}")

    state_expectations = {
        "BLOCKED_DUAL_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING": record.get("replay_result_boundary_reference_state") == "MISSING",
        "BLOCKED_DUAL_REVIEW_PAPER_RESULT_BOUNDARY_MISSING": record.get("paper_result_boundary_reference_state") == "MISSING",
        "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_DIGEST_MISSING": record.get("input_identity_digest_state") == "MISSING",
        "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_MISMATCH": record.get("input_identity_digest_match_state") == "MISMATCH",
        "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_ID_MISMATCH": record.get("runtime_resolver_snapshot_id_match_state") == "MISMATCH",
        "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISMATCH": record.get("runtime_resolver_snapshot_digest_match_state") == "MISMATCH",
        "BLOCKED_DUAL_REVIEW_STALE_REPLAY_RESULT_BOUNDARY": record.get("replay_result_boundary_reference_state") == "STALE",
        "BLOCKED_DUAL_REVIEW_STALE_PAPER_RESULT_BOUNDARY": record.get("paper_result_boundary_reference_state") == "STALE",
        "BLOCKED_DUAL_REVIEW_CONFLICT_STATE": record.get("conflict_state") == "CONFLICT_PRESENT",
        "BLOCKED_DUAL_REVIEW_SCHEMA_ERROR": record.get("schema_state") == "SCHEMA_ERROR",
        "BLOCKED_DUAL_REVIEW_LANE_MISMATCH": record.get("lane_match_state") == "MISMATCH",
        "BLOCKED_DUAL_REVIEW_TARGET_MISMATCH": record.get("target_match_state") == "MISMATCH",
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
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_DUAL_RESULT_REVIEW_NOT_SOURCE_FACT"
    ):
        failures.append("fixture.fixture_authority_class must be synthetic dual-review non-authority")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_REPLAY_RESULT_NOT_PAPER_RESULT_NOT_OWNER_REVIEW"
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
        "dual_result_review_input_contract_records": fixture.get("dual_result_review_input_contract_records"),
        "replay_paper_comparison_matrix_records": fixture.get("replay_paper_comparison_matrix_records"),
        "owner_live_promotion_handoff_block_records": fixture.get("owner_live_promotion_handoff_block_records"),
        "dual_result_review_gate_case_records": fixture.get("dual_result_review_gate_case_records"),
    }
    for name, records in groups.items():
        if not isinstance(records, list) or not records:
            failures.append(f"fixture.{name} must be a non-empty list")
            groups[name] = []

    seen_cases: set[str] = set()
    for index, record in enumerate(groups["dual_result_review_input_contract_records"]):
        if not isinstance(record, dict):
            failures.append(f"dual_result_review_input_contract_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_input_contract_record(record, label=f"dual_result_review_input_contract_records[{index}]"))

    for index, record in enumerate(groups["replay_paper_comparison_matrix_records"]):
        if not isinstance(record, dict):
            failures.append(f"replay_paper_comparison_matrix_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_comparison_matrix_record(record, label=f"replay_paper_comparison_matrix_records[{index}]"))

    for index, record in enumerate(groups["owner_live_promotion_handoff_block_records"]):
        if not isinstance(record, dict):
            failures.append(f"owner_live_promotion_handoff_block_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_handoff_block_record(record, label=f"owner_live_promotion_handoff_block_records[{index}]"))

    for index, record in enumerate(groups["dual_result_review_gate_case_records"]):
        if not isinstance(record, dict):
            failures.append(f"dual_result_review_gate_case_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_gate_case_record(record, label=f"dual_result_review_gate_case_records[{index}]"))

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - seen_cases)
    if missing_cases:
        failures.append(f"fixture missing required PR44 cases: {', '.join(missing_cases)}")
    failures.extend(canonical_atomicrows_absence_failures(repo_root, label="PR44 dual-result review fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    input_contract_schema_path: pathlib.Path = DEFAULT_INPUT_CONTRACT_SCHEMA,
    comparison_matrix_schema_path: pathlib.Path = DEFAULT_COMPARISON_MATRIX_SCHEMA,
    gate_report_schema_path: pathlib.Path = DEFAULT_GATE_REPORT_SCHEMA,
    handoff_block_schema_path: pathlib.Path = DEFAULT_HANDOFF_BLOCK_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schema_paths = {
        "input_contract": input_contract_schema_path,
        "comparison_matrix": comparison_matrix_schema_path,
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
    failures.extend(canonical_atomicrows_absence_failures(repo_root, label="PR44 dual-result review validator"))
    return failures


def _case_counts(cases: Sequence[Any]) -> dict[str, int]:
    counts = {
        "blocked_missing_result_boundary_case_count": 0,
        "blocked_identity_or_snapshot_mismatch_case_count": 0,
        "blocked_stale_conflict_schema_target_case_count": 0,
        "blocked_merge_or_decision_case_count": 0,
        "blocked_auto_promotion_or_owner_review_case_count": 0,
        "blocked_live_cash_profit_atomicrows_case_count": 0,
    }
    for record in cases:
        if not isinstance(record, dict):
            continue
        case = record.get("fixture_case")
        if case in {"BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY", "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY"}:
            counts["blocked_missing_result_boundary_case_count"] += 1
        if case in {
            "BLOCKED_MISSING_INPUT_IDENTITY_DIGEST",
            "BLOCKED_MISMATCHED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST",
            "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_ID",
            "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST",
        }:
            counts["blocked_identity_or_snapshot_mismatch_case_count"] += 1
        if case in {
            "BLOCKED_STALE_REPLAY_RESULT_BOUNDARY",
            "BLOCKED_STALE_PAPER_RESULT_BOUNDARY",
            "BLOCKED_CONFLICT_STATE",
            "BLOCKED_SCHEMA_ERROR_STATE",
            "BLOCKED_LANE_MISMATCH",
            "BLOCKED_TARGET_MISMATCH",
        }:
            counts["blocked_stale_conflict_schema_target_case_count"] += 1
        if case in {"BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM", "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM"}:
            counts["blocked_merge_or_decision_case_count"] += 1
        if case in {
            "BLOCKED_AUTO_PROMOTION_CLAIM",
            "BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_CREATION",
            "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION",
        }:
            counts["blocked_auto_promotion_or_owner_review_case_count"] += 1
        if case in {
            "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
            "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
            "BLOCKED_BLOCKER_REDUCTION_CLAIM",
        }:
            counts["blocked_live_cash_profit_atomicrows_case_count"] += 1
    return counts


def _all_fixture_records(fixture: dict[str, Any] | None) -> list[Any]:
    if fixture is None:
        return []
    records: list[Any] = []
    for key in [
        "dual_result_review_input_contract_records",
        "replay_paper_comparison_matrix_records",
        "owner_live_promotion_handoff_block_records",
        "dual_result_review_gate_case_records",
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
    input_contracts = fixture.get("dual_result_review_input_contract_records", []) if fixture else []
    matrices = fixture.get("replay_paper_comparison_matrix_records", []) if fixture else []
    handoffs = fixture.get("owner_live_promotion_handoff_block_records", []) if fixture else []
    cases = fixture.get("dual_result_review_gate_case_records", []) if fixture else []
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
        "report_version": "PR44_STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_REPORT_V1",
        "master_plan_edition": "v9.9.744",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "input_contract_record_count": len(input_contracts),
        "comparison_matrix_record_count": len(matrices),
        "handoff_block_record_count": len(handoffs),
        "gate_case_record_count": len(cases),
        **_case_counts(cases),
        "gate_state": "FAIL" if validation_failures else STATIC_GATE_STATE,
        "validation_failure_count": len(validation_failures),
        "dual_result_review_pass_next_allowed_consumer": OWNER_REVIEW_ONLY_CONSUMER,
        "dual_result_review_direct_live_consumer_allowed": False,
        "dual_result_review_direct_order_router_allowed": False,
        "dual_result_review_direct_canary_allowed": False,
        "dual_result_review_auto_promotion_allowed": False,
        "owner_review_required_before_live_eligibility": True,
        "replay_result_packet_created_flag": False,
        "paper_result_packet_created_flag": False,
        "replay_paper_results_merged_flag": False,
        "dual_result_review_decision_created_flag": False,
        "owner_live_promotion_review_created_flag": False,
        "owner_approval_receipt_created_flag": False,
        "live_eligibility_created_flag": False,
        "live_reachability_created_flag": False,
        "order_authority_created_flag": False,
        "runtime_cash_claim_created_flag": False,
        "atomicrows_bundle_hash_created_or_mutated_flag": False,
        "blocker_reduction_claim_created_flag": False,
        "profit_evidence_created_flag": False,
        "blocker_codes": blocker_codes,
        "receipt_ids_emitted": receipt_ids,
        "no_claim_flags": dict(NO_CLAIM_FLAGS),
        "validation_hook_ids": [VALIDATION_HOOK],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-contract-schema", default=str(DEFAULT_INPUT_CONTRACT_SCHEMA))
    parser.add_argument("--comparison-matrix-schema", default=str(DEFAULT_COMPARISON_MATRIX_SCHEMA))
    parser.add_argument("--gate-report-schema", default=str(DEFAULT_GATE_REPORT_SCHEMA))
    parser.add_argument("--owner-handoff-block-schema", default=str(DEFAULT_HANDOFF_BLOCK_SCHEMA))
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
        comparison_matrix_schema_path=pathlib.Path(args.comparison_matrix_schema),
        gate_report_schema_path=pathlib.Path(args.gate_report_schema),
        handoff_block_schema_path=pathlib.Path(args.owner_handoff_block_schema),
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
