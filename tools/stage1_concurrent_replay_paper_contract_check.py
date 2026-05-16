#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

SUCCESS_MARKER = "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_OK"
FAILURE_MARKER = "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_STATIC_AUDIT"

INPUT_IDENTITY_TYPE = "STAGE1_CONCURRENT_REPLAY_PAPER_INPUT_IDENTITY"
REPLAY_LANE_TYPE = "STAGE1_CONCURRENT_REPLAY_LANE_CONTRACT"
PAPER_LANE_TYPE = "STAGE1_CONCURRENT_PAPER_LANE_CONTRACT"
REPLAY_RESULT_BOUNDARY_TYPE = "STAGE1_REPLAY_RESULT_PACKET_BOUNDARY"
PAPER_RESULT_BOUNDARY_TYPE = "STAGE1_PAPER_RESULT_PACKET_BOUNDARY"
REPORT_TYPE = "STAGE1_CONCURRENT_REPLAY_PAPER_EXECUTION_GATE_REPORT"

EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
BLOCKED_STATIC_AUTHORITY = "BLOCKED_STATIC_CONTRACT_ONLY"
STATIC_GATE_STATE = "STATIC_CONCURRENT_REPLAY_PAPER_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

DEFAULT_INPUT_IDENTITY_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_paper_input_identity.schema.json"
)
DEFAULT_REPLAY_LANE_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_lane_contract.schema.json"
)
DEFAULT_PAPER_LANE_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_paper_lane_contract.schema.json"
)
DEFAULT_REPLAY_RESULT_BOUNDARY_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "replay_result_packet_boundary.schema.json"
)
DEFAULT_PAPER_RESULT_BOUNDARY_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "paper_result_packet_boundary.schema.json"
)
DEFAULT_GATE_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_paper_execution_gate_report.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/replay_paper/"
    "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
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
    "creates_replay_paper_input_lock": False,
    "executes_replay_or_paper": False,
    "creates_replay_result_packets": False,
    "creates_paper_result_packets": False,
    "creates_dual_result_review": False,
    "creates_owner_live_promotion_review": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FALSE_BOUNDARY_FIELDS = {
    "combined_result_packet_allowed_flag",
    "lane_result_merge_allowed_flag",
    "mutation_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_mutation_allowed_flag",
    "blocker_reduction_claim_allowed_flag",
    "replay_pass_starts_paper_flag",
    "replay_pass_required_before_paper_flag",
    "paper_pass_implies_live_eligibility_flag",
    "lane_execution_allowed_flag",
    "result_packet_creation_allowed_flag",
    "result_packet_merge_allowed_flag",
    "dual_result_review_allowed_flag",
    "owner_live_promotion_review_allowed_flag",
    "replay_lane_execution_allowed_flag",
    "paper_lane_execution_allowed_flag",
    "replay_result_packet_creation_allowed_flag",
    "paper_result_packet_creation_allowed_flag",
    "replay_result_packet_created_flag",
    "paper_result_packet_created_flag",
    "result_merge_allowed_flag",
    "result_merge_created_flag",
    "dual_result_review_created_flag",
    "owner_live_promotion_review_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "runtime_cash_claim_created_flag",
    "atomicrows_bundle_hash_created_or_mutated_flag",
    "blocker_reduction_claim_created_flag",
    "profit_evidence_created_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | FALSE_BOUNDARY_FIELDS | {
    "runtime_resolver_snapshot_created",
    "replay_paper_input_lock_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_result_packet_created",
    "paper_result_packet_created",
    "result_merge_created",
    "dual_result_review_created",
    "owner_live_promotion_review_created",
    "live_reachability_created",
    "order_authority_created",
    "order_execution_created",
    "runtime_cash_claim_created",
    "atomicrows_bundle_creation_claimed",
    "atomicrows_hash_creation_claimed",
    "blocker_reduction_claimed",
    "profit_evidence_created",
}

FORBIDDEN_COUNT_FIELDS = {
    "runtime_resolver_snapshot_created_count",
    "replay_execution_created_count",
    "paper_execution_created_count",
    "replay_result_packet_created_count",
    "paper_result_packet_created_count",
    "result_merge_created_count",
    "dual_result_review_created_count",
    "owner_live_promotion_review_created_count",
    "live_reachability_created_count",
    "order_execution_created_count",
    "runtime_cash_claim_created_count",
    "atomicrows_bundle_hash_created_count",
    "blocker_reduction_created_count",
    "profit_evidence_created_count",
}

FORBIDDEN_STRING_MARKERS = {
    "OFFICIAL_SOURCE_FACT_ACCEPTED",
    "REAL_ACCEPTED_SOURCE_EVIDENCE_PACKET_CREATED",
    "PRODUCTION_CONNECTOR_SEMANTIC_VALUE_POPULATED",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "REPLAY_EXECUTION_CREATED",
    "PAPER_EXECUTION_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "REPLAY_PAPER_RESULT_MERGED",
    "DUAL_RESULT_REVIEW_CREATED",
    "OWNER_LIVE_PROMOTION_REVIEW_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ORDER_EXECUTION_CREATED",
    "RUNTIME_CASH_CLAIM_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

INPUT_IDENTITY_FIELDS = {
    "input_identity_record_type",
    "input_identity_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "runtime_resolver_snapshot_id",
    "runtime_resolver_snapshot_digest",
    "runtime_resolver_input_lock_id",
    "runtime_resolver_input_lock_digest",
    "runtime_resolver_to_replay_paper_handoff_id",
    "runtime_resolver_to_replay_paper_handoff_digest",
    "runtime_resolver_handoff_gate_report_id",
    "runtime_resolver_handoff_gate_report_digest",
    "replay_paper_input_identity_digest",
    "candidate_contract_identity_set",
    "candidate_contract_identity_set_digest",
    "venue_normalization_identity_set",
    "venue_normalization_identity_set_digest",
    "source_connector_semantic_gate_receipt_refs",
    "replay_lane_input_identity_ref",
    "paper_lane_input_identity_ref",
    "input_identity_state",
    "replay_lane_and_paper_lane_must_share_input_identity_flag",
    "replay_lane_and_paper_lane_must_remain_separate_flag",
    "replay_result_packet_may_not_overwrite_paper_result_packet_flag",
    "paper_result_packet_may_not_overwrite_replay_result_packet_flag",
    "combined_result_packet_allowed_flag",
    "lane_result_merge_allowed_flag",
    "mutation_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_mutation_allowed_flag",
    "blocker_reduction_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

LANE_FIELDS_BY_LANE = {
    "REPLAY": {
        "replay_lane_contract_type",
        "replay_lane_contract_id",
        "fixture_case",
        "record_authority_class",
        "synthetic_data_notice",
        "shared_input_identity_id",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
        "runtime_resolver_input_lock_id",
        "replay_paper_input_identity_digest",
        "lane_type",
        "lane_contract_state",
        "lane_start_policy",
        "replay_pass_starts_paper_flag",
        "paper_pass_implies_live_eligibility_flag",
        "lane_execution_allowed_flag",
        "result_packet_creation_allowed_flag",
        "result_packet_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
        "blocker_codes",
        "receipt_ids",
        "no_claim_flags",
        "validation_hook_ids",
    },
    "PAPER": {
        "paper_lane_contract_type",
        "paper_lane_contract_id",
        "fixture_case",
        "record_authority_class",
        "synthetic_data_notice",
        "shared_input_identity_id",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
        "runtime_resolver_input_lock_id",
        "replay_paper_input_identity_digest",
        "lane_type",
        "lane_contract_state",
        "lane_start_policy",
        "replay_pass_required_before_paper_flag",
        "paper_pass_implies_live_eligibility_flag",
        "lane_execution_allowed_flag",
        "result_packet_creation_allowed_flag",
        "result_packet_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
        "blocker_codes",
        "receipt_ids",
        "no_claim_flags",
        "validation_hook_ids",
    },
}

RESULT_FIELDS_BY_LANE = {
    "REPLAY": {
        "replay_result_packet_boundary_type",
        "replay_result_packet_boundary_id",
        "fixture_case",
        "record_authority_class",
        "synthetic_data_notice",
        "shared_input_identity_id",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_input_lock_id",
        "replay_paper_input_identity_digest",
        "lane_type",
        "replay_result_packet_creation_authority_state",
        "immutable_after_creation_required_flag",
        "replay_lane_execution_allowed_flag",
        "replay_result_packet_creation_allowed_flag",
        "replay_result_packet_created_flag",
        "result_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
        "blocker_codes",
        "receipt_ids",
        "no_claim_flags",
        "validation_hook_ids",
    },
    "PAPER": {
        "paper_result_packet_boundary_type",
        "paper_result_packet_boundary_id",
        "fixture_case",
        "record_authority_class",
        "synthetic_data_notice",
        "shared_input_identity_id",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_input_lock_id",
        "replay_paper_input_identity_digest",
        "lane_type",
        "paper_result_packet_creation_authority_state",
        "immutable_after_creation_required_flag",
        "paper_lane_execution_allowed_flag",
        "paper_result_packet_creation_allowed_flag",
        "paper_result_packet_created_flag",
        "result_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
        "blocker_codes",
        "receipt_ids",
        "no_claim_flags",
        "validation_hook_ids",
    },
}

CASE_FIELDS = {
    "case_record_type",
    "case_id",
    "fixture_case",
    "case_authority_class",
    "synthetic_data_notice",
    "runtime_resolver_snapshot_reference_state",
    "runtime_resolver_input_lock_reference_state",
    "handoff_gate_report_reference_state",
    "snapshot_id_match_state",
    "snapshot_digest_match_state",
    "input_identity_digest_match_state",
    "candidate_contract_identity_set_match_state",
    "venue_normalization_identity_set_match_state",
    "source_connector_semantic_gate_receipt_state",
    "conflict_state",
    "schema_state",
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
    "input_identity_records",
    "replay_lane_contract_records",
    "paper_lane_contract_records",
    "replay_result_packet_boundary_records",
    "paper_result_packet_boundary_records",
    "execution_gate_case_records",
}

REPORT_FIELDS = {
    "report_type",
    "report_version",
    "master_plan_edition",
    "master_plan_sha256",
    "created_at_utc",
    "input_identity_record_count",
    "replay_lane_contract_count",
    "paper_lane_contract_count",
    "replay_result_boundary_count",
    "paper_result_boundary_count",
    "gate_case_record_count",
    "blocked_input_identity_case_count",
    "blocked_reference_case_count",
    "blocked_execution_claim_case_count",
    "blocked_result_boundary_claim_case_count",
    "blocked_merge_or_review_case_count",
    "blocked_live_cash_profit_atomicrows_case_count",
    "gate_state",
    "validation_failure_count",
    "replay_lane_execution_allowed_flag",
    "paper_lane_execution_allowed_flag",
    "replay_result_packet_created_flag",
    "paper_result_packet_created_flag",
    "result_merge_created_flag",
    "dual_result_review_created_flag",
    "owner_live_promotion_review_created_flag",
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

SCHEMA_REQUIRED_FIELDS = {
    "input_identity": {
        "type_field": "input_identity_record_type",
        "type_value": INPUT_IDENTITY_TYPE,
        "required": INPUT_IDENTITY_FIELDS,
    },
    "replay_lane": {
        "type_field": "replay_lane_contract_type",
        "type_value": REPLAY_LANE_TYPE,
        "required": LANE_FIELDS_BY_LANE["REPLAY"],
    },
    "paper_lane": {
        "type_field": "paper_lane_contract_type",
        "type_value": PAPER_LANE_TYPE,
        "required": LANE_FIELDS_BY_LANE["PAPER"],
    },
    "replay_result_boundary": {
        "type_field": "replay_result_packet_boundary_type",
        "type_value": REPLAY_RESULT_BOUNDARY_TYPE,
        "required": RESULT_FIELDS_BY_LANE["REPLAY"],
    },
    "paper_result_boundary": {
        "type_field": "paper_result_packet_boundary_type",
        "type_value": PAPER_RESULT_BOUNDARY_TYPE,
        "required": RESULT_FIELDS_BY_LANE["PAPER"],
    },
    "gate_report": {
        "type_field": "report_type",
        "type_value": REPORT_TYPE,
        "required": REPORT_FIELDS,
    },
}

EXPECTED_STATE_BY_CASE = {
    "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_ID": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_ID_MISSING",
    "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_DIGEST": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISSING",
    "BLOCKED_MISSING_RUNTIME_RESOLVER_INPUT_LOCK": "BLOCKED_RUNTIME_RESOLVER_INPUT_LOCK_MISSING",
    "BLOCKED_MISMATCHED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST": "BLOCKED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST_MISMATCH",
    "BLOCKED_MISMATCHED_SNAPSHOT_ID_BETWEEN_REPLAY_AND_PAPER": "BLOCKED_REPLAY_PAPER_RUNTIME_RESOLVER_SNAPSHOT_ID_MISMATCH",
    "BLOCKED_MISSING_HANDOFF_GATE_REPORT": "BLOCKED_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_REPORT_MISSING",
    "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT",
    "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT",
    "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT",
    "BLOCKED_SCHEMA_ERROR": "BLOCKED_SCHEMA_ERROR",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
    "BLOCKED_MISSING_SOURCE_CONNECTOR_SEMANTIC_RECEIPTS": "BLOCKED_SOURCE_CONNECTOR_SEMANTIC_GATE_RECEIPTS_MISSING",
    "BLOCKED_REPLAY_EXECUTION_CLAIM": "BLOCKED_REPLAY_EXECUTION_CLAIM",
    "BLOCKED_PAPER_EXECUTION_CLAIM": "BLOCKED_PAPER_EXECUTION_CLAIM",
    "BLOCKED_REPLAY_RESULT_PACKET_CREATION_CLAIM": "BLOCKED_REPLAY_RESULT_PACKET_CREATION_CLAIM",
    "BLOCKED_PAPER_RESULT_PACKET_CREATION_CLAIM": "BLOCKED_PAPER_RESULT_PACKET_CREATION_CLAIM",
    "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM",
    "BLOCKED_DUAL_RESULT_REVIEW_CLAIM": "BLOCKED_DUAL_RESULT_REVIEW_CLAIM",
    "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKED_BLOCKER_REDUCTION_CLAIM",
}

REQUIRED_FIXTURE_CASES = {
    "VALID_SYNTHETIC_STATIC_CONCURRENT_REPLAY_PAPER_INPUT_IDENTITY",
    "VALID_SYNTHETIC_BLOCKED_REPLAY_LANE_BOUNDARY",
    "VALID_SYNTHETIC_BLOCKED_PAPER_LANE_BOUNDARY",
    "VALID_SYNTHETIC_BLOCKED_REPLAY_RESULT_PACKET_BOUNDARY",
    "VALID_SYNTHETIC_BLOCKED_PAPER_RESULT_PACKET_BOUNDARY",
    *EXPECTED_STATE_BY_CASE,
}

CLAIM_STATE_BY_TYPE = {
    "NONE": None,
    "REPLAY_EXECUTION_AUTHORITY": "BLOCKED_REPLAY_EXECUTION_CLAIM",
    "PAPER_EXECUTION_AUTHORITY": "BLOCKED_PAPER_EXECUTION_CLAIM",
    "REPLAY_RESULT_PACKET_CREATION": "BLOCKED_REPLAY_RESULT_PACKET_CREATION_CLAIM",
    "PAPER_RESULT_PACKET_CREATION": "BLOCKED_PAPER_RESULT_PACKET_CREATION_CLAIM",
    "REPLAY_PAPER_RESULT_MERGE": "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM",
    "DUAL_RESULT_REVIEW": "BLOCKED_DUAL_RESULT_REVIEW_CLAIM",
    "LIVE_ORDER_RUNTIME_CASH_PROFIT": "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
    "ATOMICROWS_BUNDLE_HASH_MUTATION": "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKER_REDUCTION": "BLOCKED_BLOCKER_REDUCTION_CLAIM",
}


def load_json_object(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _required(schema: dict[str, Any]) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _const_value(schema: dict[str, Any], field: str) -> Any:
    prop = _properties(schema).get(field, {})
    return prop.get("const") if isinstance(prop, dict) else None


def require_exact_fields(value: dict[str, Any], fields: Iterable[str], label: str) -> list[str]:
    expected = set(fields)
    actual = set(value)
    failures: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def validate_bool_map(value: Any, expected: dict[str, bool], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from walk(item, current)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


def _master_plan_sha256(master_plan_path: pathlib.Path) -> str:
    if not master_plan_path.exists():
        return "0" * 64
    return hashlib.sha256(master_plan_path.read_bytes()).hexdigest()


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in walk(value, label):
        if key in FORBIDDEN_TRUE_FIELDS and item is not False:
            failures.append(f"{path} must be false")
        if key in FORBIDDEN_COUNT_FIELDS and item != 0:
            failures.append(f"{path} must be 0")
        if isinstance(item, str):
            upper = item.upper()
            for marker in sorted(FORBIDDEN_STRING_MARKERS):
                if marker in upper:
                    failures.append(f"{path} contains forbidden claim marker {marker}")
            if "://" in item and not path.endswith("$schema") and not path.endswith("$id"):
                failures.append(f"{path} must not contain an external locator or URL")
    return failures


def canonical_atomicrows_absence_failures(repo_root: pathlib.Path, label: str) -> list[str]:
    return validate_current_atomicrows_bundle_state(repo_root, label=label)


def validate_schema(
    schema: dict[str, Any],
    *,
    schema_key: str,
    schema_path: pathlib.Path,
) -> list[str]:
    spec = SCHEMA_REQUIRED_FIELDS[schema_key]
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{schema_path}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path}.additionalProperties must be false")
    if _const_value(schema, spec["type_field"]) != spec["type_value"]:
        failures.append(f"{schema_path}.{spec['type_field']} must be {spec['type_value']}")
    missing_required = sorted(set(spec["required"]) - _required(schema))
    if missing_required:
        failures.append(f"{schema_path} missing required fields: {', '.join(missing_required)}")
    missing_properties = sorted(set(spec["required"]) - set(_properties(schema)))
    if missing_properties:
        failures.append(f"{schema_path} missing properties: {', '.join(missing_properties)}")
    return failures


def _validate_receipts(values: Any, label: str, *, required: bool = True) -> list[str]:
    if not isinstance(values, list):
        return [f"{label} must be a list"]
    if required and not values:
        return [f"{label} must be non-empty"]
    if len(values) != len(set(values)):
        return [f"{label} must be unique"]
    return [
        f"{label} must contain non-empty strings"
        for value in values
        if not _is_non_empty_string(value)
    ]


def _validate_common_static_record(record: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def _validate_reference_match(
    record: dict[str, Any],
    ref: dict[str, Any],
    label: str,
    ref_label: str,
) -> list[str]:
    failures: list[str] = []
    simple_fields = [
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
        "runtime_resolver_input_lock_id",
        "runtime_resolver_input_lock_digest",
        "runtime_resolver_to_replay_paper_handoff_id",
        "runtime_resolver_handoff_gate_report_id",
        "replay_paper_input_identity_digest",
        "candidate_contract_identity_set",
        "candidate_contract_identity_set_digest",
        "venue_normalization_identity_set",
        "venue_normalization_identity_set_digest",
    ]
    for field in simple_fields:
        if ref.get(field) != record.get(field):
            failures.append(f"{label}.{ref_label}.{field} must match shared input identity")

    receipt_refs = record.get("source_connector_semantic_gate_receipt_refs", {})
    for field in [
        "source_evidence_gate_receipt_ids",
        "connector_semantic_gate_receipt_ids",
    ]:
        if ref.get(field) != receipt_refs.get(field):
            failures.append(f"{label}.{ref_label}.{field} must match shared receipt refs")
    return failures


def validate_input_identity_record(
    record: dict[str, Any],
    *,
    label: str = "input identity record",
) -> list[str]:
    failures = require_exact_fields(record, INPUT_IDENTITY_FIELDS, label)
    if record.get("input_identity_record_type") != INPUT_IDENTITY_TYPE:
        failures.append(f"{label}.input_identity_record_type must be {INPUT_IDENTITY_TYPE}")
    if record.get("record_authority_class") != (
        "STATIC_CONCURRENT_REPLAY_PAPER_INPUT_IDENTITY_CONTRACT_ONLY_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static input identity authority")
    if record.get("input_identity_state") != "STATIC_INPUT_IDENTITY_VALID_FOR_GATE_ONLY":
        failures.append(f"{label}.input_identity_state must be valid static gate-only")

    for field in [
        "runtime_resolver_snapshot_id",
        "runtime_resolver_input_lock_id",
        "runtime_resolver_to_replay_paper_handoff_id",
        "runtime_resolver_handoff_gate_report_id",
        "input_identity_id",
    ]:
        if not _is_non_empty_string(record.get(field)):
            failures.append(f"{label}.{field} must be present")
    for field in [
        "master_plan_sha256",
        "runtime_resolver_snapshot_digest",
        "runtime_resolver_input_lock_digest",
        "runtime_resolver_to_replay_paper_handoff_digest",
        "runtime_resolver_handoff_gate_report_digest",
        "replay_paper_input_identity_digest",
        "candidate_contract_identity_set_digest",
        "venue_normalization_identity_set_digest",
    ]:
        if not _is_sha256(record.get(field)):
            failures.append(f"{label}.{field} must be sha256-like")

    for field in ["candidate_contract_identity_set", "venue_normalization_identity_set"]:
        if not _is_non_empty_string_list(record.get(field)):
            failures.append(f"{label}.{field} must be a non-empty synthetic identity set")

    receipt_refs = record.get("source_connector_semantic_gate_receipt_refs")
    if not isinstance(receipt_refs, dict):
        failures.append(f"{label}.source_connector_semantic_gate_receipt_refs must be an object")
    else:
        for field in [
            "source_evidence_gate_receipt_ids",
            "connector_semantic_gate_receipt_ids",
        ]:
            if not _is_non_empty_string_list(receipt_refs.get(field)):
                failures.append(f"{label}.{field} must reference synthetic static gate receipts")

    replay_ref = record.get("replay_lane_input_identity_ref")
    paper_ref = record.get("paper_lane_input_identity_ref")
    if not isinstance(replay_ref, dict):
        failures.append(f"{label}.replay_lane_input_identity_ref must be an object")
    if not isinstance(paper_ref, dict):
        failures.append(f"{label}.paper_lane_input_identity_ref must be an object")
    if isinstance(replay_ref, dict) and isinstance(paper_ref, dict):
        if replay_ref.get("lane_type") != "REPLAY":
            failures.append(f"{label}.replay_lane_input_identity_ref.lane_type must be REPLAY")
        if paper_ref.get("lane_type") != "PAPER":
            failures.append(f"{label}.paper_lane_input_identity_ref.lane_type must be PAPER")
        failures.extend(_validate_reference_match(record, replay_ref, label, "replay_lane_input_identity_ref"))
        failures.extend(_validate_reference_match(record, paper_ref, label, "paper_lane_input_identity_ref"))
        if replay_ref.get("replay_paper_input_identity_digest") != paper_ref.get("replay_paper_input_identity_digest"):
            failures.append(f"{label} replay and paper identity digests must match")
        if replay_ref.get("runtime_resolver_snapshot_id") != paper_ref.get("runtime_resolver_snapshot_id"):
            failures.append(f"{label} replay and paper snapshot ids must match")
        if replay_ref.get("runtime_resolver_snapshot_digest") != paper_ref.get("runtime_resolver_snapshot_digest"):
            failures.append(f"{label} replay and paper snapshot digests must match")
        if replay_ref.get("runtime_resolver_input_lock_id") != paper_ref.get("runtime_resolver_input_lock_id"):
            failures.append(f"{label} replay and paper input lock ids must match")
        if replay_ref.get("candidate_contract_identity_set") != paper_ref.get("candidate_contract_identity_set"):
            failures.append(f"{label} replay and paper candidate contract identity sets must match")
        if replay_ref.get("venue_normalization_identity_set") != paper_ref.get("venue_normalization_identity_set"):
            failures.append(f"{label} replay and paper venue normalization identity sets must match")

    true_fields = {
        "replay_lane_and_paper_lane_must_share_input_identity_flag",
        "replay_lane_and_paper_lane_must_remain_separate_flag",
        "replay_result_packet_may_not_overwrite_paper_result_packet_flag",
        "paper_result_packet_may_not_overwrite_replay_result_packet_flag",
    }
    for field in true_fields:
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_lane_contract_record(
    record: dict[str, Any],
    *,
    lane_type: str,
    label: str = "lane contract record",
) -> list[str]:
    fields = LANE_FIELDS_BY_LANE[lane_type]
    failures = require_exact_fields(record, fields, label)
    type_field = "replay_lane_contract_type" if lane_type == "REPLAY" else "paper_lane_contract_type"
    type_value = REPLAY_LANE_TYPE if lane_type == "REPLAY" else PAPER_LANE_TYPE
    if record.get(type_field) != type_value:
        failures.append(f"{label}.{type_field} must be {type_value}")
    if record.get("lane_type") != lane_type:
        failures.append(f"{label}.lane_type must be {lane_type}")
    if record.get("lane_contract_state") != BLOCKED_STATIC_AUTHORITY:
        failures.append(f"{label}.lane_contract_state must be {BLOCKED_STATIC_AUTHORITY}")
    if record.get("lane_start_policy") != "SEPARATE_NON_SEQUENTIAL_LANE_AFTER_SHARED_INPUT_LOCK_ONLY":
        failures.append(f"{label}.lane_start_policy must keep lanes separate and non-sequential")
    if not _is_sha256(record.get("runtime_resolver_snapshot_digest")):
        failures.append(f"{label}.runtime_resolver_snapshot_digest must be sha256-like")
    if not _is_sha256(record.get("replay_paper_input_identity_digest")):
        failures.append(f"{label}.replay_paper_input_identity_digest must be sha256-like")
    if not record.get("blocker_codes"):
        failures.append(f"{label}.blocker_codes must keep lane execution blocked")
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_result_boundary_record(
    record: dict[str, Any],
    *,
    lane_type: str,
    label: str = "result boundary record",
) -> list[str]:
    fields = RESULT_FIELDS_BY_LANE[lane_type]
    failures = require_exact_fields(record, fields, label)
    type_field = (
        "replay_result_packet_boundary_type"
        if lane_type == "REPLAY"
        else "paper_result_packet_boundary_type"
    )
    type_value = REPLAY_RESULT_BOUNDARY_TYPE if lane_type == "REPLAY" else PAPER_RESULT_BOUNDARY_TYPE
    authority_field = (
        "replay_result_packet_creation_authority_state"
        if lane_type == "REPLAY"
        else "paper_result_packet_creation_authority_state"
    )
    if record.get(type_field) != type_value:
        failures.append(f"{label}.{type_field} must be {type_value}")
    if record.get("lane_type") != lane_type:
        failures.append(f"{label}.lane_type must be {lane_type}")
    if record.get(authority_field) != BLOCKED_STATIC_AUTHORITY:
        failures.append(f"{label}.{authority_field} must be {BLOCKED_STATIC_AUTHORITY}")
    if record.get("immutable_after_creation_required_flag") is not True:
        failures.append(f"{label}.immutable_after_creation_required_flag must be true")
    if not _is_sha256(record.get("replay_paper_input_identity_digest")):
        failures.append(f"{label}.replay_paper_input_identity_digest must be sha256-like")
    if not record.get("blocker_codes"):
        failures.append(f"{label}.blocker_codes must keep result packet creation blocked")
    failures.extend(_validate_common_static_record(record, label))
    return failures


def validate_gate_case_record(
    record: dict[str, Any],
    *,
    label: str = "gate case record",
) -> list[str]:
    failures = require_exact_fields(record, CASE_FIELDS, label)
    if record.get("case_record_type") != "STAGE1_CONCURRENT_REPLAY_PAPER_EXECUTION_GATE_CASE":
        failures.append(f"{label}.case_record_type is invalid")
    if record.get("case_authority_class") != "SYNTHETIC_CASE_ONLY_NOT_REPLAY_PAPER_EXECUTION_AUTHORITY":
        failures.append(f"{label}.case_authority_class must be synthetic static only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")

    case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR43 case")
    elif record.get("expected_gate_state") != expected_state:
        failures.append(f"{label}.expected_gate_state must be {expected_state}")

    state_expectations = {
        "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_ID_MISSING": record.get("runtime_resolver_snapshot_reference_state") == "MISSING_ID",
        "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISSING": record.get("runtime_resolver_snapshot_reference_state") == "MISSING_DIGEST",
        "BLOCKED_RUNTIME_RESOLVER_INPUT_LOCK_MISSING": record.get("runtime_resolver_input_lock_reference_state") == "MISSING",
        "BLOCKED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST_MISMATCH": record.get("input_identity_digest_match_state") == "MISMATCH",
        "BLOCKED_REPLAY_PAPER_RUNTIME_RESOLVER_SNAPSHOT_ID_MISMATCH": record.get("snapshot_id_match_state") == "MISMATCH",
        "BLOCKED_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_REPORT_MISSING": record.get("handoff_gate_report_reference_state") == "MISSING",
        "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT": record.get("runtime_resolver_snapshot_reference_state") == "STALE",
        "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT": record.get("runtime_resolver_snapshot_reference_state") == "SUPERSEDED",
        "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT": record.get("conflict_state") == "CONFLICT_PRESENT",
        "BLOCKED_SCHEMA_ERROR": record.get("schema_state") == "SCHEMA_ERROR",
        "BLOCKED_TARGET_MISMATCH": record.get("target_match_state") == "MISMATCH",
        "BLOCKED_SOURCE_CONNECTOR_SEMANTIC_GATE_RECEIPTS_MISSING": record.get("source_connector_semantic_gate_receipt_state") == "MISSING",
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

    if not record.get("blocker_codes"):
        failures.append(f"{label}.blocker_codes must explain blocked gate")
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_REPLAY_PAPER_EXECUTION_NOT_SOURCE_FACT"
    ):
        failures.append("fixture.fixture_authority_class must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_RUNTIME_RESOLVER_SNAPSHOT_NOT_REPLAY_PAPER_RESULT_AUTHORITY"
    ):
        failures.append("fixture.example_authority_class must be replay/paper non-authority")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append("fixture.synthetic_data_notice must mark synthetic non-authority")
    failures.extend(validate_bool_map(fixture.get("fixture_no_claim_flags"), NO_CLAIM_FLAGS, "fixture.fixture_no_claim_flags"))
    failures.extend(validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "fixture.no_claim_flags"))
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(validate_no_forbidden_claims(fixture, "fixture"))

    groups = {
        "input_identity_records": fixture.get("input_identity_records"),
        "replay_lane_contract_records": fixture.get("replay_lane_contract_records"),
        "paper_lane_contract_records": fixture.get("paper_lane_contract_records"),
        "replay_result_packet_boundary_records": fixture.get("replay_result_packet_boundary_records"),
        "paper_result_packet_boundary_records": fixture.get("paper_result_packet_boundary_records"),
        "execution_gate_case_records": fixture.get("execution_gate_case_records"),
    }
    for name, records in groups.items():
        if not isinstance(records, list) or not records:
            failures.append(f"fixture.{name} must be a non-empty list")
            groups[name] = []

    seen_cases: set[str] = set()
    for index, record in enumerate(groups["input_identity_records"]):
        if not isinstance(record, dict):
            failures.append(f"input_identity_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_input_identity_record(record, label=f"input_identity_records[{index}]"))

    for index, record in enumerate(groups["replay_lane_contract_records"]):
        if not isinstance(record, dict):
            failures.append(f"replay_lane_contract_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_lane_contract_record(
                record,
                lane_type="REPLAY",
                label=f"replay_lane_contract_records[{index}]",
            )
        )

    for index, record in enumerate(groups["paper_lane_contract_records"]):
        if not isinstance(record, dict):
            failures.append(f"paper_lane_contract_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_lane_contract_record(
                record,
                lane_type="PAPER",
                label=f"paper_lane_contract_records[{index}]",
            )
        )

    for index, record in enumerate(groups["replay_result_packet_boundary_records"]):
        if not isinstance(record, dict):
            failures.append(f"replay_result_packet_boundary_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_result_boundary_record(
                record,
                lane_type="REPLAY",
                label=f"replay_result_packet_boundary_records[{index}]",
            )
        )

    for index, record in enumerate(groups["paper_result_packet_boundary_records"]):
        if not isinstance(record, dict):
            failures.append(f"paper_result_packet_boundary_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(
            validate_result_boundary_record(
                record,
                lane_type="PAPER",
                label=f"paper_result_packet_boundary_records[{index}]",
            )
        )

    for index, record in enumerate(groups["execution_gate_case_records"]):
        if not isinstance(record, dict):
            failures.append(f"execution_gate_case_records[{index}] must be an object")
            continue
        seen_cases.add(str(record.get("fixture_case")))
        failures.extend(validate_gate_case_record(record, label=f"execution_gate_case_records[{index}]"))

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - seen_cases)
    if missing_cases:
        failures.append(f"fixture missing required PR43 cases: {', '.join(missing_cases)}")
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR43 concurrent replay/paper fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    input_identity_schema_path: pathlib.Path = DEFAULT_INPUT_IDENTITY_SCHEMA,
    replay_lane_schema_path: pathlib.Path = DEFAULT_REPLAY_LANE_SCHEMA,
    paper_lane_schema_path: pathlib.Path = DEFAULT_PAPER_LANE_SCHEMA,
    replay_result_boundary_schema_path: pathlib.Path = DEFAULT_REPLAY_RESULT_BOUNDARY_SCHEMA,
    paper_result_boundary_schema_path: pathlib.Path = DEFAULT_PAPER_RESULT_BOUNDARY_SCHEMA,
    gate_report_schema_path: pathlib.Path = DEFAULT_GATE_REPORT_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schemas = {
        "input_identity": load_json_object(input_identity_schema_path),
        "replay_lane": load_json_object(replay_lane_schema_path),
        "paper_lane": load_json_object(paper_lane_schema_path),
        "replay_result_boundary": load_json_object(replay_result_boundary_schema_path),
        "paper_result_boundary": load_json_object(paper_result_boundary_schema_path),
        "gate_report": load_json_object(gate_report_schema_path),
    }
    paths = {
        "input_identity": input_identity_schema_path,
        "replay_lane": replay_lane_schema_path,
        "paper_lane": paper_lane_schema_path,
        "replay_result_boundary": replay_result_boundary_schema_path,
        "paper_result_boundary": paper_result_boundary_schema_path,
        "gate_report": gate_report_schema_path,
    }
    for schema_key, (schema, load_failures) in schemas.items():
        failures.extend(load_failures)
        if schema is not None:
            failures.extend(
                validate_schema(
                    schema,
                    schema_key=schema_key,
                    schema_path=paths[schema_key],
                )
            )

    fixture, fixture_failures = load_json_object(fixture_path)
    failures.extend(fixture_failures)
    if fixture is not None:
        failures.extend(validate_fixture(fixture, repo_root=repo_root))
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR43 concurrent replay/paper validator"))
    return failures


def _case_counts(cases: Sequence[Any]) -> dict[str, int]:
    blocked_input_identity_case_count = 0
    blocked_reference_case_count = 0
    blocked_execution_claim_case_count = 0
    blocked_result_boundary_claim_case_count = 0
    blocked_merge_or_review_case_count = 0
    blocked_live_cash_profit_atomicrows_case_count = 0
    for record in cases:
        if not isinstance(record, dict):
            continue
        case = record.get("fixture_case")
        if case in {
            "BLOCKED_MISMATCHED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST",
            "BLOCKED_MISMATCHED_SNAPSHOT_ID_BETWEEN_REPLAY_AND_PAPER",
        }:
            blocked_input_identity_case_count += 1
        if case in {
            "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_ID",
            "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_DIGEST",
            "BLOCKED_MISSING_RUNTIME_RESOLVER_INPUT_LOCK",
            "BLOCKED_MISSING_HANDOFF_GATE_REPORT",
            "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT",
            "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT",
            "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT",
            "BLOCKED_SCHEMA_ERROR",
            "BLOCKED_TARGET_MISMATCH",
            "BLOCKED_MISSING_SOURCE_CONNECTOR_SEMANTIC_RECEIPTS",
        }:
            blocked_reference_case_count += 1
        if case in {"BLOCKED_REPLAY_EXECUTION_CLAIM", "BLOCKED_PAPER_EXECUTION_CLAIM"}:
            blocked_execution_claim_case_count += 1
        if case in {
            "BLOCKED_REPLAY_RESULT_PACKET_CREATION_CLAIM",
            "BLOCKED_PAPER_RESULT_PACKET_CREATION_CLAIM",
        }:
            blocked_result_boundary_claim_case_count += 1
        if case in {
            "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM",
            "BLOCKED_DUAL_RESULT_REVIEW_CLAIM",
        }:
            blocked_merge_or_review_case_count += 1
        if case in {
            "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
            "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
            "BLOCKED_BLOCKER_REDUCTION_CLAIM",
        }:
            blocked_live_cash_profit_atomicrows_case_count += 1
    return {
        "blocked_input_identity_case_count": blocked_input_identity_case_count,
        "blocked_reference_case_count": blocked_reference_case_count,
        "blocked_execution_claim_case_count": blocked_execution_claim_case_count,
        "blocked_result_boundary_claim_case_count": blocked_result_boundary_claim_case_count,
        "blocked_merge_or_review_case_count": blocked_merge_or_review_case_count,
        "blocked_live_cash_profit_atomicrows_case_count": blocked_live_cash_profit_atomicrows_case_count,
    }


def _all_records(fixture: dict[str, Any] | None) -> list[Any]:
    if fixture is None:
        return []
    records: list[Any] = []
    for key in [
        "input_identity_records",
        "replay_lane_contract_records",
        "paper_lane_contract_records",
        "replay_result_packet_boundary_records",
        "paper_result_packet_boundary_records",
        "execution_gate_case_records",
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
    input_identities = fixture.get("input_identity_records", []) if fixture else []
    replay_lanes = fixture.get("replay_lane_contract_records", []) if fixture else []
    paper_lanes = fixture.get("paper_lane_contract_records", []) if fixture else []
    replay_boundaries = fixture.get("replay_result_packet_boundary_records", []) if fixture else []
    paper_boundaries = fixture.get("paper_result_packet_boundary_records", []) if fixture else []
    cases = fixture.get("execution_gate_case_records", []) if fixture else []
    records = _all_records(fixture)
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
        "report_type": REPORT_TYPE,
        "report_version": "PR43_STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_REPORT_V1",
        "master_plan_edition": "v9.9.750",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "input_identity_record_count": len(input_identities),
        "replay_lane_contract_count": len(replay_lanes),
        "paper_lane_contract_count": len(paper_lanes),
        "replay_result_boundary_count": len(replay_boundaries),
        "paper_result_boundary_count": len(paper_boundaries),
        "gate_case_record_count": len(cases),
        **_case_counts(cases),
        "gate_state": "FAIL" if validation_failures else STATIC_GATE_STATE,
        "validation_failure_count": len(validation_failures),
        "replay_lane_execution_allowed_flag": False,
        "paper_lane_execution_allowed_flag": False,
        "replay_result_packet_created_flag": False,
        "paper_result_packet_created_flag": False,
        "result_merge_created_flag": False,
        "dual_result_review_created_flag": False,
        "owner_live_promotion_review_created_flag": False,
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
    parser.add_argument("--input-identity-schema", default=str(DEFAULT_INPUT_IDENTITY_SCHEMA))
    parser.add_argument("--replay-lane-schema", default=str(DEFAULT_REPLAY_LANE_SCHEMA))
    parser.add_argument("--paper-lane-schema", default=str(DEFAULT_PAPER_LANE_SCHEMA))
    parser.add_argument("--replay-result-boundary-schema", default=str(DEFAULT_REPLAY_RESULT_BOUNDARY_SCHEMA))
    parser.add_argument("--paper-result-boundary-schema", default=str(DEFAULT_PAPER_RESULT_BOUNDARY_SCHEMA))
    parser.add_argument("--gate-report-schema", default=str(DEFAULT_GATE_REPORT_SCHEMA))
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
        input_identity_schema_path=pathlib.Path(args.input_identity_schema),
        replay_lane_schema_path=pathlib.Path(args.replay_lane_schema),
        paper_lane_schema_path=pathlib.Path(args.paper_lane_schema),
        replay_result_boundary_schema_path=pathlib.Path(args.replay_result_boundary_schema),
        paper_result_boundary_schema_path=pathlib.Path(args.paper_result_boundary_schema),
        gate_report_schema_path=pathlib.Path(args.gate_report_schema),
        fixture_path=fixture_path,
    )
    failures.extend(fixture_load_failures)
    report = build_report(
        fixture=fixture,
        repo_root=repo_root,
        validation_failures=failures,
    )
    if args.out:
        _write_json(repo_root / pathlib.Path(args.out), report)
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
