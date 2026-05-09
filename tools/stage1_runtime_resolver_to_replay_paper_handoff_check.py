#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from typing import Any, Iterable, Sequence

SUCCESS_MARKER = "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_OK"
FAILURE_MARKER = "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_STATIC_AUDIT"

ALLOWLIST_TYPE = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONSUMER_ALLOWLIST"
HANDOFF_TYPE = "STAGE1_RUNTIME_RESOLVER_TO_CONCURRENT_REPLAY_PAPER_HANDOFF"
REPORT_SCHEMA_TYPE = "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_REPORT"
REPORT_TYPE = "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_REPORT"

ALLOWED_IMMEDIATE_CONSUMER = "CONCURRENT_REPLAY_PAPER_INPUT_LOCK_GATE_ONLY"
READY_STATE = "READY_FOR_CONCURRENT_REPLAY_PAPER_INPUT_LOCK_GATE_ONLY"
AUTHORIZED_STATE = "AUTHORIZED_FOR_CONCURRENT_REPLAY_PAPER_INPUT_LOCK_GATE_ONLY"
EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
STATIC_GATE_STATE = "STATIC_HANDOFF_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

DEFAULT_CONSUMER_ALLOWLIST_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
)
DEFAULT_HANDOFF_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
)
DEFAULT_HANDOFF_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
    "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
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
    "creates_replay_paper_result_packets": False,
    "creates_dual_result_review": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

ALLOWLIST_FALSE_FLAGS = {
    "direct_live_consumer_allowed_flag": False,
    "direct_dual_result_review_consumer_allowed_flag": False,
    "direct_owner_review_consumer_allowed_flag": False,
    "direct_canary_eligibility_consumer_allowed_flag": False,
    "direct_live_gate_day1_consumer_allowed_flag": False,
    "direct_dashboard_mutation_consumer_allowed_flag": False,
    "direct_order_router_consumer_allowed_flag": False,
    "runtime_cash_profit_consumer_allowed_flag": False,
    "undeclared_consumer_allowed_flag": False,
    "runtime_execution_authority_created_flag": False,
    "replay_paper_execution_authority_allowed_flag": False,
    "replay_paper_result_packet_creation_allowed_flag": False,
    "dual_result_review_creation_allowed_flag": False,
    "live_reachability_allowed_flag": False,
    "order_execution_allowed_flag": False,
    "runtime_cash_claim_allowed_flag": False,
    "profit_claim_allowed_flag": False,
    "atomicrows_bundle_mutation_allowed_flag": False,
    "blocker_reduction_claim_allowed_flag": False,
}

HANDOFF_TRUE_FLAGS = {
    "handoff_preserves_replay_paper_as_downstream_non_live_input_lock_gate_only_flag": True,
    "no_replay_or_paper_execution_created_flag": True,
    "no_replay_or_paper_result_created_flag": True,
    "no_dual_result_review_created_flag": True,
    "no_live_reachability_created_flag": True,
    "no_order_execution_created_flag": True,
    "no_runtime_cash_receipt_created_flag": True,
}

HANDOFF_FALSE_FLAGS = {
    "runtime_resolver_snapshot_mutation_allowed_flag": False,
    "new_contract_event_market_selection_allowed_flag": False,
    "replay_paper_execution_authority_allowed_flag": False,
    "replay_paper_result_packet_creation_allowed_flag": False,
    "dual_result_review_creation_allowed_flag": False,
    "live_reachability_allowed_flag": False,
    "order_execution_allowed_flag": False,
    "runtime_cash_claim_allowed_flag": False,
    "profit_claim_allowed_flag": False,
    "atomicrows_bundle_mutation_allowed_flag": False,
    "blocker_reduction_claim_allowed_flag": False,
    "source_fact_acceptance_allowed_flag": False,
    "connector_semantic_population_allowed_flag": False,
    "network_io_allowed_flag": False,
    "live_client_import_allowed_flag": False,
}

REPORT_FALSE_FLAGS = {
    "runtime_execution_authority_created_flag": False,
    "replay_paper_execution_created_flag": False,
    "replay_paper_result_packet_created_flag": False,
    "dual_result_review_created_flag": False,
    "live_reachability_created_flag": False,
    "order_authority_created_flag": False,
    "runtime_cash_claim_created_flag": False,
    "atomicrows_bundle_hash_created_or_mutated_flag": False,
    "blocker_reduction_claim_created_flag": False,
    "profit_evidence_created_flag": False,
}

FORBIDDEN_TRUE_FIELDS = (
    set(NO_CLAIM_FLAGS)
    | set(ALLOWLIST_FALSE_FLAGS)
    | set(HANDOFF_FALSE_FLAGS)
    | set(REPORT_FALSE_FLAGS)
    | {
        "runtime_resolver_snapshot_created",
        "replay_paper_input_lock_created",
        "replay_execution_created",
        "paper_execution_created",
        "replay_result_packet_created",
        "paper_result_packet_created",
        "dual_result_review_created",
        "live_reachability_created",
        "order_authority_created",
        "runtime_cash_claim_created",
        "profit_evidence_created",
        "atomicrows_bundle_mutation_claimed",
        "blocker_reduction_claimed",
    }
)

FORBIDDEN_COUNT_FIELDS = {
    "runtime_resolver_snapshot_created_count",
    "replay_paper_input_lock_created_count",
    "replay_paper_execution_created_count",
    "replay_paper_result_packet_created_count",
    "dual_result_review_created_count",
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
    "REPLAY_PAPER_INPUT_LOCK_CREATED",
    "REPLAY_EXECUTION_CREATED",
    "PAPER_EXECUTION_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "DUAL_RESULT_REVIEW_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ORDER_EXECUTION_CREATED",
    "RUNTIME_CASH_CLAIM_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

BLOCKED_CONSUMER_CLASSES = {
    "DIRECT_LIVE_CONSUMER",
    "DIRECT_DUAL_RESULT_REVIEW_CONSUMER",
    "DIRECT_OWNER_REVIEW_CONSUMER",
    "DIRECT_CANARY_ELIGIBILITY_CONSUMER",
    "DIRECT_LIVE_GATE_DAY1_CONSUMER",
    "DIRECT_DASHBOARD_MUTATION_CONSUMER",
    "DIRECT_ORDER_ROUTER_CONSUMER",
    "RUNTIME_CASH_PROFIT_CONSUMER",
    "UNDECLARED_CONSUMER",
}

EXPECTED_STATE_BY_CASE = {
    "VALID_SYNTHETIC_STATIC_HANDOFF": READY_STATE,
    "BLOCKED_DIRECT_LIVE_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_DUAL_RESULT_REVIEW_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_OWNER_REVIEW_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_CANARY_ELIGIBILITY_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_LIVE_GATE_DAY1_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_DASHBOARD_MUTATION_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_DIRECT_ORDER_ROUTER_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_RUNTIME_CASH_PROFIT_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_UNDECLARED_CONSUMER": "BLOCKED_FORBIDDEN_CONSUMER",
    "BLOCKED_STALE_SNAPSHOT": "BLOCKED_STALE_SNAPSHOT",
    "BLOCKED_STALE_INPUT_LOCK": "BLOCKED_STALE_INPUT_LOCK",
    "BLOCKED_SUPERSEDED_SNAPSHOT": "BLOCKED_SUPERSEDED_SNAPSHOT",
    "BLOCKED_CONFLICT_STATE": "BLOCKED_CONFLICT_STATE",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
    "BLOCKED_DIGEST_MISMATCH": "BLOCKED_DIGEST_MISMATCH",
    "BLOCKED_MISSING_SNAPSHOT_PACKET": "BLOCKED_SNAPSHOT_PACKET_MISSING",
    "BLOCKED_MISSING_SNAPSHOT_GATE_REPORT": "BLOCKED_SNAPSHOT_GATE_REPORT_MISSING",
    "BLOCKED_MISSING_INPUT_LOCK": "BLOCKED_INPUT_LOCK_MISSING",
    "BLOCKED_MISSING_CONSUMER_ALLOWLIST": "BLOCKED_CONSUMER_ALLOWLIST_MISSING",
    "BLOCKED_SCHEMA_ERROR": "BLOCKED_SCHEMA_ERROR",
    "BLOCKED_REPLAY_PAPER_EXECUTION_CLAIM": "BLOCKED_REPLAY_PAPER_EXECUTION_CLAIM",
    "BLOCKED_REPLAY_PAPER_RESULT_PACKET_CLAIM": "BLOCKED_REPLAY_PAPER_RESULT_PACKET_CLAIM",
    "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKED_BLOCKER_REDUCTION_CLAIM",
}

REQUIRED_FIXTURE_CASES = set(EXPECTED_STATE_BY_CASE)

CLAIM_STATE_BY_TYPE = {
    "NONE": None,
    "REPLAY_PAPER_EXECUTION_AUTHORITY": "BLOCKED_REPLAY_PAPER_EXECUTION_CLAIM",
    "REPLAY_PAPER_RESULT_PACKET_CREATION": "BLOCKED_REPLAY_PAPER_RESULT_PACKET_CLAIM",
    "LIVE_ORDER_RUNTIME_CASH_PROFIT": "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
    "ATOMICROWS_BUNDLE_HASH_MUTATION": "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
    "BLOCKER_REDUCTION": "BLOCKED_BLOCKER_REDUCTION_CLAIM",
}

ALLOWLIST_FIELDS = {
    "consumer_allowlist_type",
    "consumer_allowlist_id",
    "consumer_allowlist_digest",
    "fixture_case",
    "allowlist_authority_class",
    "synthetic_data_notice",
    "runtime_resolver_snapshot_green_next_allowed_consumer",
    "allowed_immediate_consumer_count",
    "allowed_immediate_consumers",
    "blocked_immediate_consumers",
    "concurrent_replay_paper_input_lock_gate_consumer_allowed_flag",
    *ALLOWLIST_FALSE_FLAGS,
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

BLOCKED_CONSUMER_RULE_FIELDS = {
    "consumer_id",
    "consumer_class",
    "consumer_allowed_flag",
    "authorization_state",
    "blocker_code",
}

HANDOFF_FIELDS = {
    "handoff_record_type",
    "handoff_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "master_plan_edition",
    "master_plan_sha256",
    "requested_immediate_consumer_id",
    "requested_immediate_consumer_class",
    "allowed_next_consumer_task_packet_id",
    "allowed_next_consumer_section_id",
    "handoff_state",
    "handoff_authorization_state",
    "runtime_resolver_snapshot_packet_reference",
    "runtime_resolver_snapshot_input_lock_reference",
    "runtime_resolver_snapshot_gate_report_reference",
    "runtime_resolver_snapshot_consumer_allowlist_reference",
    "upstream_digest_contract",
    "matching_identity_contract",
    "handoff_boundary_flags",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

SNAPSHOT_REFERENCE_FIELDS = {
    "snapshot_packet_id",
    "snapshot_packet_digest",
    "freshness_state",
    "revalidation_state",
    "conflict_state",
    "target_match_state",
    "schema_state",
}

INPUT_LOCK_REFERENCE_FIELDS = {
    "input_lock_id",
    "input_lock_digest",
    "snapshot_packet_id",
    "snapshot_packet_digest",
    "freshness_state",
    "revalidation_state",
    "schema_state",
}

GATE_REFERENCE_FIELDS = {
    "snapshot_gate_report_id",
    "snapshot_gate_report_digest",
    "snapshot_packet_id",
    "snapshot_packet_digest",
    "gate_state",
}

ALLOWLIST_REFERENCE_FIELDS = {
    "consumer_allowlist_id",
    "consumer_allowlist_digest",
    "snapshot_packet_id",
    "snapshot_packet_digest",
    "allowlist_state",
}

UPSTREAM_DIGEST_FIELDS = {
    "runtime_resolver_snapshot_input_lock_digest",
    "connector_semantic_binding_ledger_digest",
    "accepted_source_evidence_ledger_digest",
    "target_field_acceptance_ledger_digest",
    "runtime_resolver_input_identity_gate_digest",
    "contract_normalization_gate_digest_when_applicable",
    "candidate_scope_digest",
    "venue_scope_digest",
    "strategy_scope_digest",
    "owner_policy_snapshot_digest",
    "staleness_policy_digest",
    "liquidity_scope_digest",
    "comparability_scope_digest",
    "replay_paper_input_identity_digest",
}

MATCHING_IDENTITY_FIELDS = {
    "handoff_identity_digest",
    "handoff_identity_digest_from_snapshot_packet",
    "handoff_identity_digest_from_input_lock",
    "handoff_identity_digest_from_gate_report",
    "handoff_identity_digest_from_consumer_allowlist",
}

CASE_FIELDS = {
    "handoff_case_record_type",
    "case_id",
    "fixture_case",
    "case_authority_class",
    "synthetic_data_notice",
    "requested_immediate_consumer_id",
    "requested_immediate_consumer_class",
    "consumer_allowlist_state",
    "snapshot_packet_reference_state",
    "input_lock_reference_state",
    "snapshot_gate_report_reference_state",
    "consumer_allowlist_reference_state",
    "digest_match_state",
    "target_match_state",
    "conflict_state",
    "schema_state",
    "claim_attempt_type",
    "expected_handoff_state",
    "expected_authorization_state",
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
    "consumer_allowlist_records",
    "valid_handoff_record",
    "handoff_case_records",
}

SCHEMA_REQUIRED_FIELDS = {
    "allowlist": {
        "type_field": "consumer_allowlist_type",
        "type_value": ALLOWLIST_TYPE,
        "required": ALLOWLIST_FIELDS,
    },
    "handoff": {
        "type_field": "handoff_record_type",
        "type_value": HANDOFF_TYPE,
        "required": HANDOFF_FIELDS,
    },
    "report": {
        "type_field": "report_type",
        "type_value": REPORT_SCHEMA_TYPE,
        "required": {
            "report_type",
            "report_version",
            "master_plan_edition",
            "master_plan_sha256",
            "created_at_utc",
            "consumer_allowlist_record_count",
            "handoff_case_record_count",
            "allowed_immediate_consumer_count",
            "blocked_consumer_case_count",
            "blocked_reference_case_count",
            "blocked_claim_case_count",
            "gate_state",
            "validation_failure_count",
            *REPORT_FALSE_FLAGS,
            "blocker_codes",
            "receipt_ids_emitted",
            "no_claim_flags",
            "validation_hook_ids",
        },
    },
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


def require_exact_fields(
    value: dict[str, Any],
    fields: Iterable[str],
    label: str,
) -> list[str]:
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
            if "://" in item:
                failures.append(f"{path} must not contain an external locator or URL")
    return failures


def canonical_atomicrows_absence_failures(repo_root: pathlib.Path, label: str) -> list[str]:
    root = repo_root.resolve()
    bundle = root / pathlib.Path(*CANONICAL_ATOMICROWS_BUNDLE.parts)
    bundle_sha = root / pathlib.Path(*CANONICAL_ATOMICROWS_BUNDLE_SHA.parts)
    failures: list[str] = []
    if bundle.exists():
        failures.append(
            f"{label}: canonical AtomicRows bundle must remain absent: "
            f"{CANONICAL_ATOMICROWS_BUNDLE}"
        )
    if bundle_sha.exists():
        failures.append(
            f"{label}: canonical AtomicRows bundle hash must remain absent: "
            f"{CANONICAL_ATOMICROWS_BUNDLE_SHA}"
        )
    return failures


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

    properties = set(_properties(schema))
    missing_properties = sorted(set(spec["required"]) - properties)
    missing_required = sorted(set(spec["required"]) - _required(schema))
    if missing_properties:
        failures.append(
            f"{schema_path} missing properties: {', '.join(missing_properties)}"
        )
    if missing_required:
        failures.append(
            f"{schema_path} missing required fields: {', '.join(missing_required)}"
        )

    if schema_key in {"allowlist", "handoff", "report"}:
        if "no_claim_flags" not in properties:
            failures.append(f"{schema_path} must require no_claim_flags")
        if "validation_hook_ids" not in properties:
            failures.append(f"{schema_path} must require validation_hook_ids")
    return failures


def _validate_receipts(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{label} must be a non-empty list"]
    if len(value) != len(set(value)):
        return [f"{label} must contain unique values"]
    if not all(_is_non_empty_string(item) for item in value):
        return [f"{label} must contain non-empty strings"]
    return []


def _validate_blockers(value: Any, label: str, *, required: bool) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list"]
    if len(value) != len(set(value)):
        return [f"{label} must contain unique values"]
    if required and not value:
        return [f"{label} must explain the blocked state"]
    if not all(_is_non_empty_string(item) for item in value):
        return [f"{label} must contain non-empty strings"]
    return []


def _validate_digest_map(value: Any, fields: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, fields, label)
    for field in sorted(fields):
        if not _is_sha256(value.get(field)):
            failures.append(f"{label}.{field} must be sha256-like")
    return failures


def validate_consumer_allowlist_record(
    record: dict[str, Any],
    *,
    label: str = "consumer allowlist record",
) -> list[str]:
    failures = require_exact_fields(record, ALLOWLIST_FIELDS, label)
    if record.get("consumer_allowlist_type") != ALLOWLIST_TYPE:
        failures.append(f"{label}.consumer_allowlist_type must be {ALLOWLIST_TYPE}")
    if record.get("allowlist_authority_class") != (
        "STATIC_RUNTIME_RESOLVER_SNAPSHOT_CONSUMER_ALLOWLIST_ONLY_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append(f"{label}.allowlist_authority_class must be static only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if not _is_sha256(record.get("consumer_allowlist_digest")):
        failures.append(f"{label}.consumer_allowlist_digest must be sha256-like")
    if record.get("runtime_resolver_snapshot_green_next_allowed_consumer") != ALLOWED_IMMEDIATE_CONSUMER:
        failures.append(f"{label} must allow only {ALLOWED_IMMEDIATE_CONSUMER}")
    if record.get("allowed_immediate_consumer_count") != 1:
        failures.append(f"{label}.allowed_immediate_consumer_count must be 1")
    if record.get("allowed_immediate_consumers") != [ALLOWED_IMMEDIATE_CONSUMER]:
        failures.append(f"{label}.allowed_immediate_consumers must contain only {ALLOWED_IMMEDIATE_CONSUMER}")
    if record.get("concurrent_replay_paper_input_lock_gate_consumer_allowed_flag") is not True:
        failures.append(f"{label}.concurrent_replay_paper_input_lock_gate_consumer_allowed_flag must be true")
    for field, expected in sorted(ALLOWLIST_FALSE_FLAGS.items()):
        if record.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")

    blocked = record.get("blocked_immediate_consumers")
    if not isinstance(blocked, list) or not blocked:
        failures.append(f"{label}.blocked_immediate_consumers must be a non-empty list")
        blocked = []
    blocked_classes: set[str] = set()
    blocked_ids: set[str] = set()
    for index, rule in enumerate(blocked):
        rule_label = f"{label}.blocked_immediate_consumers[{index}]"
        if not isinstance(rule, dict):
            failures.append(f"{rule_label} must be an object")
            continue
        failures.extend(require_exact_fields(rule, BLOCKED_CONSUMER_RULE_FIELDS, rule_label))
        consumer_id = rule.get("consumer_id")
        consumer_class = rule.get("consumer_class")
        if consumer_id == ALLOWED_IMMEDIATE_CONSUMER:
            failures.append(f"{rule_label}.consumer_id must not block the only allowed consumer")
        if consumer_class not in BLOCKED_CONSUMER_CLASSES:
            failures.append(f"{rule_label}.consumer_class is not a required blocked class")
        else:
            blocked_classes.add(str(consumer_class))
        if _is_non_empty_string(consumer_id):
            blocked_ids.add(str(consumer_id))
        if rule.get("consumer_allowed_flag") is not False:
            failures.append(f"{rule_label}.consumer_allowed_flag must be false")
        if rule.get("authorization_state") != "BLOCKED_FORBIDDEN_CONSUMER":
            failures.append(f"{rule_label}.authorization_state must be BLOCKED_FORBIDDEN_CONSUMER")
        if not _is_non_empty_string(rule.get("blocker_code")):
            failures.append(f"{rule_label}.blocker_code must be non-empty")
    missing_classes = sorted(BLOCKED_CONSUMER_CLASSES - blocked_classes)
    if missing_classes:
        failures.append(f"{label} missing blocked consumer classes: {', '.join(missing_classes)}")
    if ALLOWED_IMMEDIATE_CONSUMER in blocked_ids:
        failures.append(f"{label} must not list the allowed consumer as blocked")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", required=False))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def _validate_reference_fields(
    value: Any,
    fields: set[str],
    digest_fields: set[str],
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, fields, label)
    for field in digest_fields:
        if not _is_sha256(value.get(field)):
            failures.append(f"{label}.{field} must be sha256-like")
    for field in sorted(fields - digest_fields):
        if not _is_non_empty_string(value.get(field)):
            failures.append(f"{label}.{field} must be a non-empty string")
    return failures


def validate_handoff_record(
    record: dict[str, Any],
    *,
    allowlist_records: Sequence[dict[str, Any]] | None = None,
    label: str = "handoff record",
) -> list[str]:
    failures = require_exact_fields(record, HANDOFF_FIELDS, label)
    if record.get("handoff_record_type") != HANDOFF_TYPE:
        failures.append(f"{label}.handoff_record_type must be {HANDOFF_TYPE}")
    if record.get("record_authority_class") != (
        "STATIC_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CONTRACT_ONLY_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append(f"{label}.record_authority_class must be static only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if not _is_sha256(record.get("master_plan_sha256")):
        failures.append(f"{label}.master_plan_sha256 must be sha256-like")
    if record.get("allowed_next_consumer_task_packet_id") != ALLOWED_IMMEDIATE_CONSUMER:
        failures.append(f"{label}.allowed_next_consumer_task_packet_id must be {ALLOWED_IMMEDIATE_CONSUMER}")
    if record.get("allowed_next_consumer_section_id") != "0X.4T_INPUT_LOCK_GATE_ONLY":
        failures.append(f"{label}.allowed_next_consumer_section_id must be input-lock-gate only")

    state = record.get("handoff_state")
    requested_consumer = record.get("requested_immediate_consumer_id")
    if state == READY_STATE:
        if requested_consumer != ALLOWED_IMMEDIATE_CONSUMER:
            failures.append(f"{label}.requested_immediate_consumer_id is not allowlisted")
        if record.get("handoff_authorization_state") != AUTHORIZED_STATE:
            failures.append(f"{label}.handoff_authorization_state must be {AUTHORIZED_STATE}")
        failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", required=False))
        if record.get("blocker_codes"):
            failures.append(f"{label}.blocker_codes must be empty for ready handoff")
    else:
        failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", required=True))

    snapshot = record.get("runtime_resolver_snapshot_packet_reference")
    input_lock = record.get("runtime_resolver_snapshot_input_lock_reference")
    gate = record.get("runtime_resolver_snapshot_gate_report_reference")
    allowlist_ref = record.get("runtime_resolver_snapshot_consumer_allowlist_reference")
    failures.extend(
        _validate_reference_fields(
            snapshot,
            SNAPSHOT_REFERENCE_FIELDS,
            {"snapshot_packet_digest"},
            f"{label}.runtime_resolver_snapshot_packet_reference",
        )
    )
    failures.extend(
        _validate_reference_fields(
            input_lock,
            INPUT_LOCK_REFERENCE_FIELDS,
            {"input_lock_digest", "snapshot_packet_digest"},
            f"{label}.runtime_resolver_snapshot_input_lock_reference",
        )
    )
    failures.extend(
        _validate_reference_fields(
            gate,
            GATE_REFERENCE_FIELDS,
            {"snapshot_gate_report_digest", "snapshot_packet_digest"},
            f"{label}.runtime_resolver_snapshot_gate_report_reference",
        )
    )
    failures.extend(
        _validate_reference_fields(
            allowlist_ref,
            ALLOWLIST_REFERENCE_FIELDS,
            {"consumer_allowlist_digest", "snapshot_packet_digest"},
            f"{label}.runtime_resolver_snapshot_consumer_allowlist_reference",
        )
    )

    if all(isinstance(item, dict) for item in [snapshot, input_lock, gate, allowlist_ref]):
        assert isinstance(snapshot, dict)
        assert isinstance(input_lock, dict)
        assert isinstance(gate, dict)
        assert isinstance(allowlist_ref, dict)
        if state == READY_STATE:
            expected_states = {
                "snapshot.freshness_state": snapshot.get("freshness_state") == "CURRENT",
                "snapshot.revalidation_state": snapshot.get("revalidation_state") == "CURRENT",
                "snapshot.conflict_state": snapshot.get("conflict_state") == "NO_CONFLICT",
                "snapshot.target_match_state": snapshot.get("target_match_state") == "MATCHED",
                "snapshot.schema_state": snapshot.get("schema_state") == "SCHEMA_VALID",
                "input_lock.freshness_state": input_lock.get("freshness_state") == "CURRENT",
                "input_lock.revalidation_state": input_lock.get("revalidation_state") == "CURRENT",
                "input_lock.schema_state": input_lock.get("schema_state") == "SCHEMA_VALID",
                "gate.gate_state": gate.get("gate_state") == "GREEN",
                "allowlist.allowlist_state": allowlist_ref.get("allowlist_state") == "ALLOWLISTED",
            }
            for state_name, is_valid in expected_states.items():
                if not is_valid:
                    failures.append(f"{label}.{state_name} must be ready/current for ready handoff")

        snapshot_id = snapshot.get("snapshot_packet_id")
        snapshot_digest = snapshot.get("snapshot_packet_digest")
        for ref_label, ref in {
            "input_lock": input_lock,
            "gate_report": gate,
            "consumer_allowlist": allowlist_ref,
        }.items():
            if ref.get("snapshot_packet_id") != snapshot_id:
                failures.append(f"{label}.{ref_label}.snapshot_packet_id must match snapshot packet id")
            if ref.get("snapshot_packet_digest") != snapshot_digest:
                failures.append(f"{label}.{ref_label}.snapshot_packet_digest must match snapshot packet digest")

        if allowlist_records:
            allowlist_by_id = {
                item.get("consumer_allowlist_id"): item
                for item in allowlist_records
                if isinstance(item, dict)
            }
            allowlist_record = allowlist_by_id.get(allowlist_ref.get("consumer_allowlist_id"))
            if allowlist_record is None:
                failures.append(f"{label}.consumer_allowlist_reference must reference a declared allowlist")
            elif allowlist_record.get("consumer_allowlist_digest") != allowlist_ref.get("consumer_allowlist_digest"):
                failures.append(f"{label}.consumer_allowlist_digest must match declared allowlist digest")

    upstream = record.get("upstream_digest_contract")
    failures.extend(_validate_digest_map(upstream, UPSTREAM_DIGEST_FIELDS, f"{label}.upstream_digest_contract"))
    if isinstance(upstream, dict) and isinstance(input_lock, dict):
        if upstream.get("runtime_resolver_snapshot_input_lock_digest") != input_lock.get("input_lock_digest"):
            failures.append(f"{label}.upstream_digest_contract.runtime_resolver_snapshot_input_lock_digest must match input lock digest")

    matching = record.get("matching_identity_contract")
    failures.extend(_validate_digest_map(matching, MATCHING_IDENTITY_FIELDS, f"{label}.matching_identity_contract"))
    if isinstance(matching, dict):
        values = [matching.get(field) for field in MATCHING_IDENTITY_FIELDS]
        if len(set(values)) != 1:
            failures.append(f"{label}.matching_identity_contract digests must all match")

    flags = record.get("handoff_boundary_flags")
    if not isinstance(flags, dict):
        failures.append(f"{label}.handoff_boundary_flags must be an object")
    else:
        failures.extend(
            validate_bool_map(
                flags,
                {**HANDOFF_TRUE_FLAGS, **HANDOFF_FALSE_FLAGS},
                f"{label}.handoff_boundary_flags",
            )
        )
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def validate_handoff_case_record(
    record: dict[str, Any],
    *,
    label: str = "handoff case record",
) -> list[str]:
    failures = require_exact_fields(record, CASE_FIELDS, label)
    if record.get("handoff_case_record_type") != "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CASE":
        failures.append(f"{label}.handoff_case_record_type is invalid")
    if record.get("case_authority_class") != "SYNTHETIC_CASE_ONLY_NOT_RUNTIME_AUTHORITY":
        failures.append(f"{label}.case_authority_class must be synthetic static only")
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")

    case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR42 handoff case")
    elif record.get("expected_handoff_state") != expected_state:
        failures.append(f"{label}.expected_handoff_state must be {expected_state}")

    requested_consumer = record.get("requested_immediate_consumer_id")
    consumer_state = record.get("consumer_allowlist_state")
    if expected_state == READY_STATE:
        if requested_consumer != ALLOWED_IMMEDIATE_CONSUMER:
            failures.append(f"{label}.requested_immediate_consumer_id must be the only allowed consumer")
        if consumer_state != "ALLOWLISTED":
            failures.append(f"{label}.consumer_allowlist_state must be ALLOWLISTED")
        if record.get("expected_authorization_state") != AUTHORIZED_STATE:
            failures.append(f"{label}.expected_authorization_state must be {AUTHORIZED_STATE}")
        if record.get("blocker_codes"):
            failures.append(f"{label}.blocker_codes must be empty for valid handoff")
    else:
        if not record.get("blocker_codes"):
            failures.append(f"{label}.blocker_codes must explain blocked handoff")
        if record.get("expected_authorization_state") != expected_state:
            failures.append(f"{label}.expected_authorization_state must match blocked state")

    if consumer_state == "BLOCKED_FORBIDDEN_CONSUMER":
        if record.get("requested_immediate_consumer_class") not in BLOCKED_CONSUMER_CLASSES:
            failures.append(f"{label}.requested_immediate_consumer_class must be a blocked consumer class")
        if requested_consumer == ALLOWED_IMMEDIATE_CONSUMER:
            failures.append(f"{label}.requested_immediate_consumer_id must not be allowed for forbidden consumer case")
        if expected_state != "BLOCKED_FORBIDDEN_CONSUMER":
            failures.append(f"{label}.expected_handoff_state must block forbidden consumers")
    elif consumer_state == "ALLOWLISTED":
        if requested_consumer != ALLOWED_IMMEDIATE_CONSUMER:
            failures.append(f"{label}.requested_immediate_consumer_id is not allowlisted")
    elif consumer_state != "MISSING":
        failures.append(f"{label}.consumer_allowlist_state is invalid")

    state_expectations = {
        "BLOCKED_STALE_SNAPSHOT": record.get("snapshot_packet_reference_state") == "STALE",
        "BLOCKED_STALE_INPUT_LOCK": record.get("input_lock_reference_state") == "STALE",
        "BLOCKED_SUPERSEDED_SNAPSHOT": record.get("snapshot_packet_reference_state") == "SUPERSEDED",
        "BLOCKED_CONFLICT_STATE": record.get("conflict_state") == "CONFLICT_PRESENT",
        "BLOCKED_TARGET_MISMATCH": record.get("target_match_state") == "MISMATCH",
        "BLOCKED_DIGEST_MISMATCH": record.get("digest_match_state") == "MISMATCH",
        "BLOCKED_SNAPSHOT_PACKET_MISSING": record.get("snapshot_packet_reference_state") == "MISSING",
        "BLOCKED_SNAPSHOT_GATE_REPORT_MISSING": record.get("snapshot_gate_report_reference_state") == "MISSING",
        "BLOCKED_INPUT_LOCK_MISSING": record.get("input_lock_reference_state") == "MISSING",
        "BLOCKED_CONSUMER_ALLOWLIST_MISSING": (
            record.get("consumer_allowlist_state") == "MISSING"
            and record.get("consumer_allowlist_reference_state") == "MISSING"
        ),
        "BLOCKED_SCHEMA_ERROR": record.get("schema_state") == "SCHEMA_ERROR",
    }
    if expected_state in state_expectations and not state_expectations[expected_state]:
        failures.append(f"{label}.{case} state fields do not match expected blocked state")

    claim_type = record.get("claim_attempt_type")
    if claim_type not in CLAIM_STATE_BY_TYPE:
        failures.append(f"{label}.claim_attempt_type is invalid")
    else:
        claim_state = CLAIM_STATE_BY_TYPE[claim_type]
        if claim_state is None:
            if expected_state in {
                "BLOCKED_REPLAY_PAPER_EXECUTION_CLAIM",
                "BLOCKED_REPLAY_PAPER_RESULT_PACKET_CLAIM",
                "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM",
                "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
                "BLOCKED_BLOCKER_REDUCTION_CLAIM",
            }:
                failures.append(f"{label}.claim_attempt_type must explain claim-blocked case")
        elif expected_state != claim_state:
            failures.append(f"{label}.claim_attempt_type does not match expected blocked claim state")

    if expected_state == READY_STATE:
        ready_checks = {
            "snapshot_packet_reference_state": "PRESENT_CURRENT",
            "input_lock_reference_state": "PRESENT_CURRENT",
            "snapshot_gate_report_reference_state": "PRESENT_GREEN",
            "consumer_allowlist_reference_state": "PRESENT_ALLOWLISTED",
            "digest_match_state": "MATCHED",
            "target_match_state": "MATCHED",
            "conflict_state": "NO_CONFLICT",
            "schema_state": "SCHEMA_VALID",
            "claim_attempt_type": "NONE",
        }
        for field, expected in ready_checks.items():
            if record.get(field) != expected:
                failures.append(f"{label}.{field} must be {expected} for valid handoff")

    failures.extend(_validate_blockers(record.get("blocker_codes"), f"{label}.blocker_codes", required=expected_state != READY_STATE))
    failures.extend(_validate_receipts(record.get("receipt_ids"), f"{label}.receipt_ids"))
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_HANDOFF_NOT_SOURCE_FACT":
        failures.append("fixture.fixture_authority_class must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_RUNTIME_RESOLVER_SNAPSHOT_NOT_REPLAY_PAPER_AUTHORITY"
    ):
        failures.append("fixture.example_authority_class must be handoff non-authority")
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

    allowlists = fixture.get("consumer_allowlist_records")
    if not isinstance(allowlists, list) or not allowlists:
        failures.append("fixture.consumer_allowlist_records must be a non-empty list")
        allowlists = []
    for index, record in enumerate(allowlists):
        if not isinstance(record, dict):
            failures.append(f"consumer_allowlist_records[{index}] must be an object")
            continue
        failures.extend(
            validate_consumer_allowlist_record(
                record,
                label=f"consumer_allowlist_records[{index}]",
            )
        )

    valid_handoff = fixture.get("valid_handoff_record")
    if not isinstance(valid_handoff, dict):
        failures.append("fixture.valid_handoff_record must be an object")
    else:
        failures.extend(
            validate_handoff_record(
                valid_handoff,
                allowlist_records=allowlists,
                label="valid_handoff_record",
            )
        )

    cases = fixture.get("handoff_case_records")
    if not isinstance(cases, list) or not cases:
        failures.append("fixture.handoff_case_records must be a non-empty list")
        cases = []

    seen_cases: set[str] = set()
    for index, record in enumerate(cases):
        if not isinstance(record, dict):
            failures.append(f"handoff_case_records[{index}] must be an object")
            continue
        failures.extend(
            validate_handoff_case_record(
                record,
                label=f"handoff_case_records[{index}]",
            )
        )
        if isinstance(record.get("fixture_case"), str):
            seen_cases.add(record["fixture_case"])

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - seen_cases)
    if missing_cases:
        failures.append(f"fixture missing required PR42 handoff cases: {', '.join(missing_cases)}")
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR42 handoff fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    consumer_allowlist_schema_path: pathlib.Path = DEFAULT_CONSUMER_ALLOWLIST_SCHEMA,
    handoff_contract_schema_path: pathlib.Path = DEFAULT_HANDOFF_CONTRACT_SCHEMA,
    handoff_report_schema_path: pathlib.Path = DEFAULT_HANDOFF_REPORT_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schemas = {
        "allowlist": load_json_object(consumer_allowlist_schema_path),
        "handoff": load_json_object(handoff_contract_schema_path),
        "report": load_json_object(handoff_report_schema_path),
    }
    paths = {
        "allowlist": consumer_allowlist_schema_path,
        "handoff": handoff_contract_schema_path,
        "report": handoff_report_schema_path,
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
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR42 handoff validator"))
    return failures


def _case_counts(cases: Sequence[Any]) -> dict[str, int]:
    blocked_consumer_case_count = 0
    blocked_reference_case_count = 0
    blocked_claim_case_count = 0
    for record in cases:
        if not isinstance(record, dict):
            continue
        state = record.get("expected_handoff_state")
        if state == "BLOCKED_FORBIDDEN_CONSUMER":
            blocked_consumer_case_count += 1
        if state in {
            "BLOCKED_STALE_SNAPSHOT",
            "BLOCKED_STALE_INPUT_LOCK",
            "BLOCKED_SUPERSEDED_SNAPSHOT",
            "BLOCKED_CONFLICT_STATE",
            "BLOCKED_TARGET_MISMATCH",
            "BLOCKED_DIGEST_MISMATCH",
            "BLOCKED_SNAPSHOT_PACKET_MISSING",
            "BLOCKED_INPUT_LOCK_MISSING",
            "BLOCKED_SNAPSHOT_GATE_REPORT_MISSING",
            "BLOCKED_CONSUMER_ALLOWLIST_MISSING",
            "BLOCKED_SCHEMA_ERROR",
        }:
            blocked_reference_case_count += 1
        if record.get("claim_attempt_type") != "NONE":
            blocked_claim_case_count += 1
    return {
        "blocked_consumer_case_count": blocked_consumer_case_count,
        "blocked_reference_case_count": blocked_reference_case_count,
        "blocked_claim_case_count": blocked_claim_case_count,
    }


def build_report(
    *,
    fixture: dict[str, Any] | None,
    repo_root: pathlib.Path,
    validation_failures: Sequence[str],
    master_plan_path: pathlib.Path = DEFAULT_MASTER_PLAN,
) -> dict[str, Any]:
    allowlists = fixture.get("consumer_allowlist_records", []) if fixture else []
    cases = fixture.get("handoff_case_records", []) if fixture else []
    valid_handoff = fixture.get("valid_handoff_record", {}) if fixture else {}
    blocker_codes = sorted(
        {
            blocker
            for group in [allowlists, cases, [valid_handoff]]
            for record in group
            if isinstance(record, dict)
            for blocker in record.get("blocker_codes", [])
            if isinstance(blocker, str)
        }
    )
    receipt_ids = sorted(
        {
            receipt
            for group in [allowlists, cases, [valid_handoff]]
            for record in group
            if isinstance(record, dict)
            for receipt in record.get("receipt_ids", [])
            if isinstance(receipt, str)
        }
    )
    return {
        "report_type": REPORT_TYPE,
        "report_version": "PR42_STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_REPORT_V1",
        "master_plan_edition": "v9.9.750",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "consumer_allowlist_record_count": len(allowlists),
        "handoff_case_record_count": len(cases),
        "allowed_immediate_consumer_count": 1,
        **_case_counts(cases),
        "gate_state": "FAIL" if validation_failures else STATIC_GATE_STATE,
        "validation_failure_count": len(validation_failures),
        "runtime_execution_authority_created_flag": False,
        "replay_paper_execution_created_flag": False,
        "replay_paper_result_packet_created_flag": False,
        "dual_result_review_created_flag": False,
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
    parser.add_argument("--consumer-allowlist-schema", default=str(DEFAULT_CONSUMER_ALLOWLIST_SCHEMA))
    parser.add_argument("--handoff-contract-schema", default=str(DEFAULT_HANDOFF_CONTRACT_SCHEMA))
    parser.add_argument("--handoff-report-schema", default=str(DEFAULT_HANDOFF_REPORT_SCHEMA))
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
        consumer_allowlist_schema_path=pathlib.Path(args.consumer_allowlist_schema),
        handoff_contract_schema_path=pathlib.Path(args.handoff_contract_schema),
        handoff_report_schema_path=pathlib.Path(args.handoff_report_schema),
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
