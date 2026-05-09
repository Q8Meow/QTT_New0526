#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from typing import Any, Iterable, Sequence

SUCCESS_MARKER = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_OK"
FAILURE_MARKER = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_FAILED"
VALIDATION_HOOK = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_STATIC_AUDIT"

INPUT_LOCK_TYPE = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_INPUT_LOCK"
MANIFEST_TYPE = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_MANIFEST"
CONSUMER_CONTRACT_TYPE = "STAGE1_RUNTIME_RESOLVER_CONSUMER_CONTRACT"
GATE_REPORT_TYPE = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_GATE_REPORT"
REPORT_TYPE = "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_REPORT"

EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"
BLOCKED_STATIC_AUTHORITY = "BLOCKED_STATIC_CONTRACT_ONLY"
VALID_INPUT_LOCK_STATE = "STATIC_INPUT_LOCK_VALID_FOR_GATE_ONLY"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

DEFAULT_INPUT_LOCK_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_input_lock.schema.json"
)
DEFAULT_MANIFEST_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_manifest.schema.json"
)
DEFAULT_CONSUMER_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_consumer_contract.schema.json"
)
DEFAULT_GATE_REPORT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_gate_report.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/runtime_resolver/"
    "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
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
    "creates_replay_paper_result_packets": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

RUNTIME_FALSE_FIELDS = {
    "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
    "runtime_resolver_snapshot_allowed_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "replay_paper_input_allowed_flag",
    "replay_paper_may_consume_runtime_resolver_data_from_pr41_flag",
    "live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag",
    "order_router_may_consume_runtime_resolver_data_from_pr41_flag",
    "dashboard_live_readiness_claim_allowed_flag",
    "direct_runtime_use_allowed_flag",
    "live_client_import_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "atomicrows_bundle_mutation_allowed_flag",
    "blocker_reduction_claim_allowed_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | RUNTIME_FALSE_FIELDS | {
    "accepted_source_fact_created",
    "accepted_source_packet_created",
    "accepted_source_evidence_packet_created",
    "real_accepted_source_evidence_packet_created",
    "production_connector_semantic_value_populated",
    "connector_semantic_value_populated",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_result_packet_created",
    "paper_result_packet_created",
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
    "replay_paper_execution_created_count",
    "replay_paper_result_packet_created_count",
    "live_reachability_created_count",
    "order_execution_created_count",
    "runtime_cash_claim_created_count",
    "atomicrows_bundle_created_count",
    "blocker_reduction_created_count",
    "profit_evidence_created_count",
}

FORBIDDEN_STRING_MARKERS = {
    "OFFICIAL_SOURCE_FACT_ACCEPTED",
    "ACCEPTED_SOURCE_FACT_CREATED",
    "REAL_ACCEPTED_SOURCE_EVIDENCE_PACKET_CREATED",
    "PRODUCTION_CONNECTOR_SEMANTIC_VALUE_POPULATED",
    "CONNECTOR_SEMANTIC_BOUND",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ORDER_EXECUTION_CREATED",
    "RUNTIME_CASH_CLAIM_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

INPUT_LOCK_FIELDS = {
    "runtime_resolver_snapshot_input_lock_type",
    "input_lock_id",
    "input_lock_record_digest",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "snapshot_creation_authority_state",
    "input_lock_validation_state",
    "accepted_source_evidence_export_record_ids",
    "accepted_source_evidence_export_record_digests",
    "connector_semantic_binding_ledger_record_ids",
    "connector_semantic_binding_ledger_record_digests",
    "source_to_connector_field_binding_record_ids",
    "source_to_connector_field_binding_record_digests",
    "canonical_contract_venue_identity_normalization_record_ids",
    "canonical_contract_venue_identity_normalization_record_digests",
    "target_field_paths",
    "target_field_path_hashes",
    "venue_ids",
    "applicability_scope",
    "freshness_state",
    "revalidation_state",
    "conflict_state",
    "contract_normalization_state",
    "consumer_authorization_state",
    "upstream_record_state",
    "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
    "runtime_resolver_snapshot_allowed_flag",
    "replay_paper_input_allowed_flag",
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

MANIFEST_FIELDS = {
    "runtime_resolver_snapshot_manifest_type",
    "runtime_resolver_snapshot_manifest_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "snapshot_creation_authority_state",
    "input_lock_id",
    "input_lock_digest",
    "connector_semantic_binding_ledger_record_ids",
    "connector_semantic_binding_ledger_record_digests",
    "accepted_source_evidence_export_record_ids",
    "accepted_source_evidence_export_record_digests",
    "source_to_connector_field_binding_record_ids",
    "venue_ids",
    "target_field_paths",
    "target_field_path_hashes",
    "applicability_scope",
    "revalidation_state",
    "conflict_state",
    "contract_normalization_state",
    "consumer_authorization_state",
    "runtime_resolver_snapshot_allowed_flag",
    "replay_paper_input_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

CONSUMER_CONTRACT_FIELDS = {
    "runtime_resolver_consumer_contract_type",
    "runtime_resolver_consumer_contract_id",
    "fixture_case",
    "contract_authority_class",
    "synthetic_data_notice",
    "consumer_id",
    "consumer_class",
    "consumer_authorization_state",
    "runtime_resolver_schema_gate_may_validate_synthetic_fixture_records_only_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "replay_paper_may_consume_runtime_resolver_data_from_pr41_flag",
    "live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag",
    "order_router_may_consume_runtime_resolver_data_from_pr41_flag",
    "dashboard_may_display_blocked_static_gate_reports_only_flag",
    "dashboard_live_readiness_claim_allowed_flag",
    "direct_runtime_use_allowed_flag",
    "live_client_import_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "profit_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

GATE_REPORT_FIELDS = {
    "runtime_resolver_snapshot_gate_report_type",
    "runtime_resolver_snapshot_gate_report_id",
    "fixture_case",
    "report_authority_class",
    "synthetic_data_notice",
    "snapshot_manifest_count",
    "input_lock_count",
    "consumer_contract_count",
    "stale_binding_count",
    "conflict_binding_count",
    "target_mismatch_count",
    "missing_accepted_source_evidence_export_linkage_count",
    "missing_connector_semantic_binding_linkage_count",
    "missing_source_to_connector_field_binding_linkage_count",
    "missing_digest_or_hash_count",
    "cross_venue_target_field_misuse_count",
    "snapshot_creation_attempt_count",
    "replay_paper_consumption_attempt_count",
    "live_order_runtime_cash_profit_claim_attempt_count",
    "atomicrows_mutation_claim_count",
    "blocker_reduction_claim_count",
    "gate_state",
    "snapshot_creation_authority_state",
    "runtime_resolver_snapshot_allowed_flag",
    "replay_paper_input_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids_emitted",
    "no_claim_flags",
    "validation_hook_ids",
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
    "input_lock_records",
    "snapshot_manifest_records",
    "consumer_contract_records",
    "snapshot_gate_report_records",
}

SCHEMA_REQUIRED_FIELDS = {
    "input_lock": {
        "type_field": "runtime_resolver_snapshot_input_lock_type",
        "type_value": INPUT_LOCK_TYPE,
        "required": INPUT_LOCK_FIELDS,
    },
    "manifest": {
        "type_field": "runtime_resolver_snapshot_manifest_type",
        "type_value": MANIFEST_TYPE,
        "required": MANIFEST_FIELDS,
    },
    "consumer": {
        "type_field": "runtime_resolver_consumer_contract_type",
        "type_value": CONSUMER_CONTRACT_TYPE,
        "required": CONSUMER_CONTRACT_FIELDS,
    },
    "gate_report": {
        "type_field": "runtime_resolver_snapshot_gate_report_type",
        "type_value": GATE_REPORT_TYPE,
        "required": GATE_REPORT_FIELDS,
    },
}

EXPECTED_INPUT_LOCK_STATE_BY_CASE = {
    "VALID_SYNTHETIC_STATIC_INPUT_LOCK": VALID_INPUT_LOCK_STATE,
    "BLOCKED_STALE_UPSTREAM_BINDING": "BLOCKED_STALE_UPSTREAM_BINDING",
    "BLOCKED_CONFLICT_UPSTREAM_BINDING": "BLOCKED_CONFLICT_UPSTREAM_BINDING",
    "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
    "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE": (
        "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE"
    ),
    "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE": (
        "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE"
    ),
    "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE": (
        "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE"
    ),
    "BLOCKED_MISSING_DIGEST_OR_HASH": "BLOCKED_MISSING_DIGEST_OR_HASH",
    "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE": (
        "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE"
    ),
    "BLOCKED_SUPERSEDED_UPSTREAM_RECORD": "BLOCKED_SUPERSEDED_UPSTREAM_RECORD",
    "BLOCKED_SCHEMA_ERROR": "BLOCKED_SCHEMA_ERROR",
    "BLOCKED_UNDECLARED_CONSUMER": "BLOCKED_UNDECLARED_CONSUMER",
}

REQUIRED_FIXTURE_CASES = set(EXPECTED_INPUT_LOCK_STATE_BY_CASE) | {
    "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_CREATION_ATTEMPT",
    "BLOCKED_REPLAY_PAPER_CONSUMPTION_ATTEMPT",
    "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM_ATTEMPT",
    "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM",
}

EXPECTED_CONSUMER_STATE_BY_CLASS = {
    "STATIC_SCHEMA_GATE_SYNTHETIC_FIXTURE_VALIDATION_ONLY": (
        "AUTHORIZED_SYNTHETIC_STATIC_VALIDATION_ONLY"
    ),
    "DASHBOARD_BLOCKED_STATIC_GATE_REPORT_DISPLAY_ONLY": (
        "AUTHORIZED_BLOCKED_STATIC_REPORT_DISPLAY_ONLY"
    ),
    "RUNTIME_RESOLVER_SNAPSHOT_CREATION_ATTEMPT": "BLOCKED_STATIC_CONTRACT_ONLY",
    "REPLAY_PAPER_DIRECT_CONSUMER_ATTEMPT": "BLOCKED_REPLAY_PAPER_DIRECT_CONSUMPTION",
    "LIVE_CANARY_LIVE_ARBITRAGE_CONSUMER_ATTEMPT": "BLOCKED_LIVE_CONSUMPTION",
    "ORDER_ROUTER_CONSUMER_ATTEMPT": "BLOCKED_ORDER_AUTHORITY",
    "RUNTIME_CASH_PROFIT_CLAIM_ATTEMPT": "BLOCKED_RUNTIME_CASH_OR_PROFIT_CLAIM",
    "ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM_ATTEMPT": "BLOCKED_ATOMICROWS_MUTATION",
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


def _schema_requires_hook(schema: dict[str, Any]) -> bool:
    prop = _properties(schema).get("validation_hook_ids", {})
    if not isinstance(prop, dict):
        return False
    ref = prop.get("$ref")
    if isinstance(ref, str) and ref.endswith("/validation_hook_ids"):
        return True
    items = prop.get("items", {})
    return isinstance(items, dict) and items.get("const") == VALIDATION_HOOK


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


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def missing_reference(value: Any) -> bool:
    return not isinstance(value, str) or not value or value.startswith("MISSING_")


def _any_missing_reference(values: Any) -> bool:
    return not isinstance(values, list) or any(missing_reference(value) for value in values)


def _all_sha256(values: Any) -> bool:
    return isinstance(values, list) and bool(values) and all(_is_sha256(value) for value in values)


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
            if "CANDIDATE_SOURCE" in upper and (
                key.startswith("accepted_source_evidence")
                or "accepted_source_evidence" in path
            ):
                failures.append(f"{path} must not treat candidate source evidence as accepted")
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
    missing_required = sorted(set(spec["required"]) - _required(schema))
    if missing_required:
        failures.append(
            f"{schema_path} missing required fields: {', '.join(missing_required)}"
        )
    if not _schema_requires_hook(schema):
        failures.append(f"{schema_path}.validation_hook_ids must require {VALIDATION_HOOK}")
    return failures


def _validate_common_record(record: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    receipts = record.get("receipt_ids") or record.get("receipt_ids_emitted")
    if not isinstance(receipts, list) or not receipts:
        failures.append(f"{label}.receipt_ids must be a non-empty list")
    blockers = record.get("blocker_codes")
    if not isinstance(blockers, list):
        failures.append(f"{label}.blocker_codes must be a list")
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(validate_no_forbidden_claims(record, label))
    return failures


def _validate_scope(
    record: dict[str, Any],
    label: str,
    *,
    allow_target_mismatch: bool = False,
    require_cross_venue_misuse: bool = False,
) -> list[str]:
    scope = record.get("applicability_scope")
    if not isinstance(scope, dict):
        return [f"{label}.applicability_scope must be an object"]
    failures = require_exact_fields(
        scope,
        {
            "scope_id",
            "scope_authority_class",
            "venue_id",
            "requested_venue_id",
            "target_field_paths",
            "wildcard_scope_allowed",
            "cross_venue_scope_allowed",
        },
        f"{label}.applicability_scope",
    )
    if scope.get("scope_authority_class") != "SYNTHETIC_SCOPE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY":
        failures.append(f"{label}.applicability_scope.scope_authority_class must be synthetic")
    if scope.get("wildcard_scope_allowed") is not False:
        failures.append(f"{label}.applicability_scope.wildcard_scope_allowed must be false")
    if scope.get("cross_venue_scope_allowed") is not False:
        failures.append(f"{label}.applicability_scope.cross_venue_scope_allowed must be false")
    target_mismatch = scope.get("target_field_paths") != record.get("target_field_paths")
    if target_mismatch and not allow_target_mismatch:
        failures.append(f"{label}.applicability_scope.target_field_paths must match target_field_paths")
    if not target_mismatch and allow_target_mismatch:
        failures.append(f"{label} target mismatch case must show a target field mismatch")

    venue_ids = record.get("venue_ids")
    requested_venue = scope.get("requested_venue_id")
    scope_venue = scope.get("venue_id")
    cross_venue_misuse = (
        requested_venue != scope_venue
        or not isinstance(venue_ids, list)
        or requested_venue not in venue_ids
        or scope_venue not in venue_ids
    )
    if cross_venue_misuse and not require_cross_venue_misuse:
        failures.append(f"{label}.applicability_scope must not cross venue boundaries")
    if not cross_venue_misuse and require_cross_venue_misuse:
        failures.append(f"{label} cross-venue fixture must show cross-venue misuse")
    return failures


def _validate_target_hashes(
    record: dict[str, Any],
    label: str,
    *,
    allow_missing_hash: bool = False,
) -> list[str]:
    paths = record.get("target_field_paths")
    hashes = record.get("target_field_path_hashes")
    if not isinstance(paths, list) or not paths:
        return [f"{label}.target_field_paths must be a non-empty list"]
    if not isinstance(hashes, list) or len(hashes) != len(paths):
        return [f"{label}.target_field_path_hashes must match target_field_paths length"]
    failures: list[str] = []
    missing_or_bad_hash = any(not _is_sha256(value) for value in hashes)
    if missing_or_bad_hash and not allow_missing_hash:
        failures.append(f"{label}.target_field_path_hashes must be sha256-like")
    if allow_missing_hash and not missing_or_bad_hash:
        failures.append(f"{label} missing-digest case must include a missing target field hash")
    if not missing_or_bad_hash:
        for path_text, hash_text in zip(paths, hashes):
            if not isinstance(path_text, str) or _hash_text(path_text) != hash_text:
                failures.append(f"{label}.target_field_path_hashes must match target_field_paths")
    return failures


def _validate_linkage(
    record: dict[str, Any],
    label: str,
    *,
    case: str,
) -> list[str]:
    failures: list[str] = []
    accepted_missing = _any_missing_reference(
        record.get("accepted_source_evidence_export_record_ids")
    )
    connector_missing = _any_missing_reference(
        record.get("connector_semantic_binding_ledger_record_ids")
    )
    source_to_connector_missing = _any_missing_reference(
        record.get("source_to_connector_field_binding_record_ids")
    )
    digest_missing = not all(
        _all_sha256(record.get(field))
        for field in [
            "accepted_source_evidence_export_record_digests",
            "connector_semantic_binding_ledger_record_digests",
            "source_to_connector_field_binding_record_digests",
            "canonical_contract_venue_identity_normalization_record_digests",
        ]
    )
    expected_missing = {
        "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE": accepted_missing,
        "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE": connector_missing,
        "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE": source_to_connector_missing,
        "BLOCKED_MISSING_DIGEST_OR_HASH": digest_missing,
    }
    for fixture_case, missing in expected_missing.items():
        if case == fixture_case and not missing:
            failures.append(f"{label}.{fixture_case} must show its missing prerequisite")
        if case != fixture_case and missing:
            failures.append(f"{label} has missing prerequisite inconsistent with {case}")
    if case == "VALID_SYNTHETIC_STATIC_INPUT_LOCK":
        if accepted_missing or connector_missing or source_to_connector_missing or digest_missing:
            failures.append(f"{label} valid records require all linkage records and digests")
    return failures


def validate_input_lock_record(record: dict[str, Any], *, label: str = "input lock record") -> list[str]:
    failures = require_exact_fields(record, INPUT_LOCK_FIELDS, label)
    if record.get("runtime_resolver_snapshot_input_lock_type") != INPUT_LOCK_TYPE:
        failures.append(f"{label}.runtime_resolver_snapshot_input_lock_type must be {INPUT_LOCK_TYPE}")
    failures.extend(_validate_common_record(record, label))
    if not _is_sha256(record.get("input_lock_record_digest")):
        failures.append(f"{label}.input_lock_record_digest must be sha256-like")
    if record.get("snapshot_creation_authority_state") != BLOCKED_STATIC_AUTHORITY:
        failures.append(
            f"{label}.snapshot_creation_authority_state must remain {BLOCKED_STATIC_AUTHORITY} in PR41"
        )

    case = record.get("fixture_case")
    expected_state = EXPECTED_INPUT_LOCK_STATE_BY_CASE.get(case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR41 input-lock case")
        expected_state = record.get("input_lock_validation_state")
    if record.get("input_lock_validation_state") != expected_state:
        failures.append(f"{label}.input_lock_validation_state must be {expected_state} for {case}")

    blockers = record.get("blocker_codes")
    if record.get("input_lock_validation_state") != VALID_INPUT_LOCK_STATE:
        if not blockers:
            failures.append(f"{label}.blocker_codes must explain blocked records")
    else:
        if record.get("upstream_record_state") != "APPROVED_STATIC_RECORDS_REFERENCED_ONLY":
            failures.append(f"{label}.upstream_record_state must be approved static references")
        if record.get("freshness_state") != "CURRENT_SYNTHETIC_STATIC":
            failures.append(f"{label}.freshness_state must be current for valid static input lock")
        if record.get("revalidation_state") != "CURRENT":
            failures.append(f"{label}.revalidation_state must be CURRENT")
        if record.get("conflict_state") != "NO_CONFLICT":
            failures.append(f"{label}.conflict_state must be NO_CONFLICT")
        if record.get("consumer_authorization_state") != "AUTHORIZED_STATIC_GATE_INPUT_ONLY":
            failures.append(f"{label}.consumer_authorization_state must be gate-only authorized")

    failures.extend(_validate_linkage(record, label, case=str(case)))
    failures.extend(
        _validate_target_hashes(
            record,
            label,
            allow_missing_hash=case == "BLOCKED_MISSING_DIGEST_OR_HASH",
        )
    )
    failures.extend(
        _validate_scope(
            record,
            label,
            allow_target_mismatch=case == "BLOCKED_TARGET_MISMATCH",
            require_cross_venue_misuse=case == "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE",
        )
    )

    case_expectations = {
        "BLOCKED_STALE_UPSTREAM_BINDING": record.get("freshness_state") == "STALE_REVALIDATION_REQUIRED",
        "BLOCKED_CONFLICT_UPSTREAM_BINDING": record.get("conflict_state") == "CONFLICT_PRESENT",
        "BLOCKED_SUPERSEDED_UPSTREAM_RECORD": record.get("revalidation_state") == "SUPERSEDED",
        "BLOCKED_SCHEMA_ERROR": record.get("upstream_record_state") == "SCHEMA_ERROR",
        "BLOCKED_UNDECLARED_CONSUMER": record.get("consumer_authorization_state") == "BLOCKED_UNDECLARED_CONSUMER",
    }
    if case in case_expectations and not case_expectations[case]:
        failures.append(f"{label}.{case} state fields do not match the blocked case")
    return failures


def validate_manifest_record(record: dict[str, Any], *, label: str = "manifest record") -> list[str]:
    failures = require_exact_fields(record, MANIFEST_FIELDS, label)
    if record.get("runtime_resolver_snapshot_manifest_type") != MANIFEST_TYPE:
        failures.append(f"{label}.runtime_resolver_snapshot_manifest_type must be {MANIFEST_TYPE}")
    failures.extend(_validate_common_record(record, label))
    if record.get("snapshot_creation_authority_state") != BLOCKED_STATIC_AUTHORITY:
        failures.append(
            f"{label}.snapshot_creation_authority_state must remain {BLOCKED_STATIC_AUTHORITY} in PR41"
        )
    if not _is_sha256(record.get("input_lock_digest")):
        failures.append(f"{label}.input_lock_digest must be sha256-like")
    for field in [
        "connector_semantic_binding_ledger_record_digests",
        "accepted_source_evidence_export_record_digests",
    ]:
        if not _all_sha256(record.get(field)):
            failures.append(f"{label}.{field} must contain sha256-like digests")
    for field in [
        "accepted_source_evidence_export_record_ids",
        "connector_semantic_binding_ledger_record_ids",
        "source_to_connector_field_binding_record_ids",
    ]:
        if _any_missing_reference(record.get(field)):
            failures.append(f"{label}.{field} must reference declared static prerequisites")
    failures.extend(_validate_target_hashes(record, label))
    failures.extend(_validate_scope(record, label))
    if not record.get("blocker_codes"):
        failures.append(f"{label}.blocker_codes must keep snapshot creation blocked")
    return failures


def validate_consumer_contract_record(
    record: dict[str, Any],
    *,
    label: str = "consumer contract record",
) -> list[str]:
    failures = require_exact_fields(record, CONSUMER_CONTRACT_FIELDS, label)
    if record.get("runtime_resolver_consumer_contract_type") != CONSUMER_CONTRACT_TYPE:
        failures.append(f"{label}.runtime_resolver_consumer_contract_type must be {CONSUMER_CONTRACT_TYPE}")
    failures.extend(_validate_common_record(record, label))
    for field, expected in {
        "runtime_resolver_schema_gate_may_validate_synthetic_fixture_records_only_flag": True,
        "dashboard_may_display_blocked_static_gate_reports_only_flag": True,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
        "replay_paper_may_consume_runtime_resolver_data_from_pr41_flag": False,
        "live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag": False,
        "order_router_may_consume_runtime_resolver_data_from_pr41_flag": False,
        "dashboard_live_readiness_claim_allowed_flag": False,
        "direct_runtime_use_allowed_flag": False,
        "live_client_import_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
        "runtime_cash_claim_allowed_flag": False,
        "profit_claim_allowed_flag": False,
    }.items():
        if record.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")

    consumer_class = record.get("consumer_class")
    expected_state = EXPECTED_CONSUMER_STATE_BY_CLASS.get(consumer_class)
    if expected_state is None:
        failures.append(f"{label}.consumer_class is invalid")
    elif record.get("consumer_authorization_state") != expected_state:
        failures.append(
            f"{label}.consumer_authorization_state must be {expected_state} for {consumer_class}"
        )
    blockers = record.get("blocker_codes")
    if expected_state and expected_state.startswith("AUTHORIZED"):
        if blockers:
            failures.append(f"{label}.blocker_codes must be empty for static authorized consumers")
    elif not blockers:
        failures.append(f"{label}.blocker_codes must explain blocked consumers")
    return failures


def validate_gate_report_record(
    record: dict[str, Any],
    *,
    label: str = "gate report record",
) -> list[str]:
    failures = require_exact_fields(record, GATE_REPORT_FIELDS, label)
    if record.get("runtime_resolver_snapshot_gate_report_type") != GATE_REPORT_TYPE:
        failures.append(f"{label}.runtime_resolver_snapshot_gate_report_type must be {GATE_REPORT_TYPE}")
    failures.extend(_validate_common_record(record, label))
    if record.get("gate_state") != BLOCKED_STATIC_AUTHORITY:
        failures.append(f"{label}.gate_state must remain {BLOCKED_STATIC_AUTHORITY}")
    if record.get("snapshot_creation_authority_state") != BLOCKED_STATIC_AUTHORITY:
        failures.append(f"{label}.snapshot_creation_authority_state must remain blocked")
    return failures


def _case_counts(input_locks: list[dict[str, Any]], consumers: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "stale_binding_count": sum(
            record.get("fixture_case") == "BLOCKED_STALE_UPSTREAM_BINDING"
            for record in input_locks
        ),
        "conflict_binding_count": sum(
            record.get("fixture_case") == "BLOCKED_CONFLICT_UPSTREAM_BINDING"
            for record in input_locks
        ),
        "target_mismatch_count": sum(
            record.get("fixture_case") == "BLOCKED_TARGET_MISMATCH"
            for record in input_locks
        ),
        "missing_accepted_source_evidence_export_linkage_count": sum(
            record.get("fixture_case")
            == "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE"
            for record in input_locks
        ),
        "missing_connector_semantic_binding_linkage_count": sum(
            record.get("fixture_case")
            == "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE"
            for record in input_locks
        ),
        "missing_source_to_connector_field_binding_linkage_count": sum(
            record.get("fixture_case")
            == "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE"
            for record in input_locks
        ),
        "missing_digest_or_hash_count": sum(
            record.get("fixture_case") == "BLOCKED_MISSING_DIGEST_OR_HASH"
            for record in input_locks
        ),
        "cross_venue_target_field_misuse_count": sum(
            record.get("fixture_case") == "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE"
            for record in input_locks
        ),
        "snapshot_creation_attempt_count": sum(
            record.get("consumer_class") == "RUNTIME_RESOLVER_SNAPSHOT_CREATION_ATTEMPT"
            for record in consumers
        ),
        "replay_paper_consumption_attempt_count": sum(
            record.get("consumer_class") == "REPLAY_PAPER_DIRECT_CONSUMER_ATTEMPT"
            for record in consumers
        ),
        "live_order_runtime_cash_profit_claim_attempt_count": sum(
            record.get("consumer_class")
            in {
                "LIVE_CANARY_LIVE_ARBITRAGE_CONSUMER_ATTEMPT",
                "ORDER_ROUTER_CONSUMER_ATTEMPT",
                "RUNTIME_CASH_PROFIT_CLAIM_ATTEMPT",
            }
            for record in consumers
        ),
        "atomicrows_mutation_claim_count": sum(
            record.get("consumer_class")
            == "ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM_ATTEMPT"
            for record in consumers
        ),
    }


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT":
        failures.append("fixture.fixture_authority_class must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_RUNTIME_RESOLVER_AUTHORITY"
    ):
        failures.append("fixture.example_authority_class must be runtime resolver non-authority")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append("fixture.synthetic_data_notice must mark synthetic non-authority")
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(validate_bool_map(fixture.get("fixture_no_claim_flags"), NO_CLAIM_FLAGS, "fixture.fixture_no_claim_flags"))
    failures.extend(validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "fixture.no_claim_flags"))
    failures.extend(validate_no_forbidden_claims(fixture, "fixture"))

    input_locks = fixture.get("input_lock_records")
    manifests = fixture.get("snapshot_manifest_records")
    consumers = fixture.get("consumer_contract_records")
    gate_reports = fixture.get("snapshot_gate_report_records")
    if not isinstance(input_locks, list) or not input_locks:
        failures.append("fixture.input_lock_records must be a non-empty list")
        input_locks = []
    if not isinstance(manifests, list) or not manifests:
        failures.append("fixture.snapshot_manifest_records must be a non-empty list")
        manifests = []
    if not isinstance(consumers, list) or not consumers:
        failures.append("fixture.consumer_contract_records must be a non-empty list")
        consumers = []
    if not isinstance(gate_reports, list) or not gate_reports:
        failures.append("fixture.snapshot_gate_report_records must be a non-empty list")
        gate_reports = []

    input_cases: set[str] = set()
    for index, record in enumerate(input_locks):
        if not isinstance(record, dict):
            failures.append(f"input_lock_records[{index}] must be an object")
            continue
        failures.extend(
            validate_input_lock_record(record, label=f"input_lock_records[{index}]")
        )
        if isinstance(record.get("fixture_case"), str):
            input_cases.add(record["fixture_case"])

    all_cases = set(input_cases)
    for index, record in enumerate(manifests):
        if not isinstance(record, dict):
            failures.append(f"snapshot_manifest_records[{index}] must be an object")
            continue
        failures.extend(
            validate_manifest_record(record, label=f"snapshot_manifest_records[{index}]")
        )
        if isinstance(record.get("fixture_case"), str):
            all_cases.add(record["fixture_case"])

    for index, record in enumerate(consumers):
        if not isinstance(record, dict):
            failures.append(f"consumer_contract_records[{index}] must be an object")
            continue
        failures.extend(
            validate_consumer_contract_record(
                record,
                label=f"consumer_contract_records[{index}]",
            )
        )
        if isinstance(record.get("fixture_case"), str):
            all_cases.add(record["fixture_case"])

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - all_cases)
    if missing_cases:
        failures.append(f"fixture missing required fixture cases: {', '.join(missing_cases)}")

    counts = _case_counts(input_locks, consumers)
    for index, record in enumerate(gate_reports):
        if not isinstance(record, dict):
            failures.append(f"snapshot_gate_report_records[{index}] must be an object")
            continue
        failures.extend(
            validate_gate_report_record(
                record,
                label=f"snapshot_gate_report_records[{index}]",
            )
        )
        expected_counts = {
            "input_lock_count": len(input_locks),
            "snapshot_manifest_count": len(manifests),
            "consumer_contract_count": len(consumers),
            **counts,
        }
        for field, expected in sorted(expected_counts.items()):
            if record.get(field) != expected:
                failures.append(f"snapshot_gate_report_records[{index}].{field} must be {expected}")

    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR41 runtime resolver snapshot fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    input_lock_schema_path: pathlib.Path = DEFAULT_INPUT_LOCK_SCHEMA,
    manifest_schema_path: pathlib.Path = DEFAULT_MANIFEST_SCHEMA,
    consumer_contract_schema_path: pathlib.Path = DEFAULT_CONSUMER_CONTRACT_SCHEMA,
    gate_report_schema_path: pathlib.Path = DEFAULT_GATE_REPORT_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    schemas = {
        "input_lock": load_json_object(input_lock_schema_path),
        "manifest": load_json_object(manifest_schema_path),
        "consumer": load_json_object(consumer_contract_schema_path),
        "gate_report": load_json_object(gate_report_schema_path),
    }
    paths = {
        "input_lock": input_lock_schema_path,
        "manifest": manifest_schema_path,
        "consumer": consumer_contract_schema_path,
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
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR41 runtime resolver snapshot validator"))
    return failures


def _master_plan_sha256(master_plan_path: pathlib.Path) -> str:
    if not master_plan_path.exists():
        return "MASTER_PLAN_MISSING_NO_SHA_AUTHORITY"
    return hashlib.sha256(master_plan_path.read_bytes()).hexdigest()


def build_report(
    *,
    fixture: dict[str, Any] | None,
    repo_root: pathlib.Path,
    validation_failures: Sequence[str],
    master_plan_path: pathlib.Path = DEFAULT_MASTER_PLAN,
) -> dict[str, Any]:
    input_locks = fixture.get("input_lock_records", []) if fixture else []
    manifests = fixture.get("snapshot_manifest_records", []) if fixture else []
    consumers = fixture.get("consumer_contract_records", []) if fixture else []
    counts = _case_counts(input_locks, consumers)
    blocker_codes = sorted(
        {
            blocker
            for group in [input_locks, manifests, consumers]
            for record in group
            if isinstance(record, dict)
            for blocker in record.get("blocker_codes", [])
            if isinstance(blocker, str)
        }
    )
    receipt_ids = sorted(
        {
            receipt
            for group in [input_locks, manifests, consumers]
            for record in group
            if isinstance(record, dict)
            for receipt in record.get("receipt_ids", [])
            if isinstance(receipt, str)
        }
    )
    return {
        "report_type": REPORT_TYPE,
        "master_plan_edition": "v9.9.742",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "input_lock_count": len(input_locks),
        "snapshot_manifest_count": len(manifests),
        "consumer_contract_count": len(consumers),
        **counts,
        "runtime_resolver_snapshot_allowed_flag": False,
        "replay_paper_input_allowed_flag": False,
        "live_reachability_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "runtime_cash_claim_allowed_flag": False,
        "gate_state": "FAIL" if validation_failures else BLOCKED_STATIC_AUTHORITY,
        "validation_failure_count": len(validation_failures),
        "blocker_codes": blocker_codes,
        "receipt_ids_emitted": receipt_ids,
    }


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-lock-schema", default=str(DEFAULT_INPUT_LOCK_SCHEMA))
    parser.add_argument("--manifest-schema", default=str(DEFAULT_MANIFEST_SCHEMA))
    parser.add_argument("--consumer-contract-schema", default=str(DEFAULT_CONSUMER_CONTRACT_SCHEMA))
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
        input_lock_schema_path=pathlib.Path(args.input_lock_schema),
        manifest_schema_path=pathlib.Path(args.manifest_schema),
        consumer_contract_schema_path=pathlib.Path(args.consumer_contract_schema),
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
