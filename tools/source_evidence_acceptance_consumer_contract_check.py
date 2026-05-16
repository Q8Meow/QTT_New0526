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

SUCCESS_MARKER = "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_VALIDATION_OK"
FAILURE_MARKER = "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_VALIDATION_FAILED"
VALIDATION_HOOK = "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_AUDIT"

EXPORT_RECORD_TYPE = "STAGE1_ACCEPTED_SOURCE_EVIDENCE_EXPORT_RECORD"
LEDGER_RECORD_TYPE = "STAGE1_TARGET_FIELD_ACCEPTANCE_LEDGER_RECORD"
CONSUMER_CONTRACT_TYPE = "STAGE1_ACCEPTED_SOURCE_EVIDENCE_CONSUMER_CONTRACT"
AUTHORIZED_STATE = "AUTHORIZED_FOR_CONNECTOR_SEMANTIC_BINDING_NONLIVE_ONLY"
BLOCKED_STALE = "BLOCKED_STALE"
BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
BLOCKED_TARGET_MISMATCH = "BLOCKED_TARGET_MISMATCH"
BLOCKED_CONSUMER_NOT_DECLARED = "BLOCKED_CONSUMER_NOT_DECLARED"

EXPECTED_ACCEPTED_PACKET_AUTHORITY = (
    "SYNTHETIC_ACCEPTED_SOURCE_EVIDENCE_PACKET_REFERENCE_ONLY_NOT_REAL_FACT_AUTHORITY"
)
EXPECTED_PACKET_VERSION = "SYNTHETIC_ACCEPTED_PACKET_REFERENCE_V1_NOT_REAL_SOURCE_FACT"
EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

DEFAULT_CONSUMER_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/source_evidence/acceptance/accepted_source_evidence_consumer_contract.schema.json"
)
DEFAULT_LEDGER_SCHEMA = pathlib.Path(
    "src/qtt/source_evidence/acceptance/stage1_target_field_acceptance_ledger_record.schema.json"
)
DEFAULT_EXPORT_SCHEMA = pathlib.Path(
    "src/qtt/source_evidence/acceptance/stage1_accepted_source_evidence_export_record.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/acceptance_consumer_contract/"
    "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
)

NO_CLAIM_FLAGS = {
    "accepts_source_facts": False,
    "creates_real_accepted_source_evidence": False,
    "creates_accepted_source_packets": False,
    "populates_connector_semantic_values": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FIXTURE_NO_CLAIM_FLAGS = {
    "retrieves_source_facts": False,
    **NO_CLAIM_FLAGS,
}

RUNTIME_FALSE_FIELDS = {
    "runtime_resolver_snapshot_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "connector_semantic_value_population_allowed_flag",
    "connector_semantic_binding_allowed_directly_from_ledger_flag",
    "candidate_evidence_packet_is_accepted_source_evidence_flag",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | {
    "retrieves_source_facts",
    "accepts_real_source_facts",
    "accepted_source_fact_created",
    "accepted_source_packet_created",
    "accepted_source_evidence_packet_created",
    "connector_semantic_value_populated",
    "connector_semantic_values_populated",
    "runtime_resolver_snapshot_created",
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
    "accepted_source_fact_created_count",
    "real_accepted_source_evidence_packet_count",
    "connector_semantic_value_populated_count",
    "runtime_resolver_snapshot_created_count",
    "live_reachability_created_count",
    "order_authority_created_count",
    "runtime_cash_claim_created_count",
    "atomicrows_bundle_created_count",
    "blocker_reduction_count",
    "profit_evidence_created_count",
}

FORBIDDEN_STRING_MARKERS = {
    "OFFICIAL_SOURCE_FACT_ACCEPTED",
    "ACCEPTED_SOURCE_FACT_CREATED",
    "REAL_ACCEPTED_SOURCE_EVIDENCE_PACKET_CREATED",
    "CONNECTOR_SEMANTIC_VALUE_POPULATED",
    "VENUE_API_VALUE_POPULATED",
    "FEE_SEMANTIC_VALUE_POPULATED",
    "TICK_SEMANTIC_VALUE_POPULATED",
    "RATE_LIMIT_VALUE_POPULATED",
    "SETTLEMENT_VALUE_POPULATED",
    "ORDER_ENTRY_VALUE_POPULATED",
    "PRIVATE_STATE_VALUE_POPULATED",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

ACCEPTED_PACKET_CURRENT_STATES = {
    "CURRENT",
    "STALE_REVALIDATION_REQUIRED",
    "SUPERSEDED",
    "BLOCKED_CONFLICT",
    "BLOCKED_SCHEMA_ERROR",
}

CONSUMER_AUTHORIZATION_STATES = {
    AUTHORIZED_STATE,
    BLOCKED_STALE,
    BLOCKED_CONFLICT,
    BLOCKED_TARGET_MISMATCH,
    BLOCKED_CONSUMER_NOT_DECLARED,
}

REQUIRED_FIXTURE_CASES = {
    "CURRENT_AUTHORIZED_NONLIVE",
    "BLOCKED_STALE",
    "BLOCKED_CONFLICT",
    "BLOCKED_TARGET_MISMATCH",
    "BLOCKED_UNDECLARED_CONSUMER",
    "BLOCKED_SUPERSEDED",
    "BLOCKED_SCHEMA_ERROR",
    "BLOCKED_FORBIDDEN_RUNTIME_ATTEMPT",
}

COMMON_RECORD_FIELDS = {
    "fixture_case",
    "synthetic_data_notice",
    "accepted_source_evidence_packet_id",
    "accepted_source_evidence_packet_digest",
    "accepted_source_evidence_packet_version",
    "accepted_source_evidence_packet_authority_class",
    "source_target_id",
    "venue_id",
    "target_field_path",
    "target_field_path_hash",
    "target_field_path_hash_algorithm",
    "accepted_packet_applicability_scope",
    "accepted_packet_conflict_state",
    "accepted_packet_revalidation_due_condition",
    "accepted_packet_current_state",
    "authorized_consumer_task_ids",
    "runtime_resolver_snapshot_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

LEDGER_FIELDS = {
    "target_field_acceptance_ledger_record_type",
    "target_field_acceptance_ledger_record_id",
    "target_field_acceptance_ledger_record_digest",
    "record_authority_class",
    "consumer_contract_required_flag",
    "connector_semantic_binding_allowed_directly_from_ledger_flag",
} | COMMON_RECORD_FIELDS

EXPORT_FIELDS = {
    "accepted_source_evidence_export_record_type",
    "accepted_source_evidence_export_record_id",
    "record_authority_class",
    "target_field_acceptance_ledger_record_id",
    "target_field_acceptance_ledger_record_digest",
    "requested_consumer_task_id",
    "requested_target_field_path",
    "consumer_authorization_state",
    "connector_semantic_binding_allowed_flag",
    "connector_semantic_value_population_allowed_flag",
} | COMMON_RECORD_FIELDS

CONTRACT_FIELDS = {
    "accepted_source_evidence_consumer_contract_type",
    "accepted_source_evidence_consumer_contract_id",
    "fixture_case",
    "contract_authority_class",
    "synthetic_data_notice",
    "accepted_source_evidence_export_record_id",
    "target_field_acceptance_ledger_record_id",
    "source_target_id",
    "venue_id",
    "target_field_path",
    "requested_target_field_path",
    "requested_consumer_task_id",
    "authorized_consumer_task_ids",
    "candidate_evidence_packet_is_accepted_source_evidence_flag",
    "accepted_packet_current_state",
    "consumer_authorization_state",
    "connector_semantic_binding_allowed_flag",
    "nonlive_schema_level_downstream_work_only_flag",
    "connector_semantic_value_population_allowed_flag",
    "runtime_resolver_snapshot_allowed_flag",
    "live_reachability_allowed_flag",
    "order_execution_allowed_flag",
    "runtime_cash_claim_allowed_flag",
    "blocker_codes",
    "receipt_ids",
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
    "target_field_acceptance_ledger_records",
    "accepted_source_evidence_export_records",
    "consumer_contract_records",
}

SCHEMA_REQUIRED_FIELDS = {
    "consumer": {
        "accepted_source_evidence_consumer_contract_type": CONSUMER_CONTRACT_TYPE,
        "required": CONTRACT_FIELDS,
    },
    "ledger": {
        "target_field_acceptance_ledger_record_type": LEDGER_RECORD_TYPE,
        "required": LEDGER_FIELDS,
    },
    "export": {
        "accepted_source_evidence_export_record_type": EXPORT_RECORD_TYPE,
        "required": EXPORT_FIELDS,
    },
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


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: Iterable[str],
    label: str,
) -> list[str]:
    expected = set(expected_fields)
    actual = set(value)
    failures: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _validate_bool_map(value: Any, expected: dict[str, bool], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = _require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def _walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _canonical_path(root: pathlib.Path, rel_path: pathlib.PurePosixPath) -> pathlib.Path:
    return root.resolve() / pathlib.Path(*rel_path.parts)


def _atomicrows_absence_failures(repo_root: pathlib.Path, label: str) -> list[str]:
    return validate_current_atomicrows_bundle_state(repo_root, label=label)


def _validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(value, label):
        if key in FORBIDDEN_TRUE_FIELDS and item is not False:
            failures.append(f"{path} must be false")
        if key in RUNTIME_FALSE_FIELDS and item is not False:
            failures.append(f"{path} must be false")
        if key in FORBIDDEN_COUNT_FIELDS and item != 0:
            failures.append(f"{path} must be 0")
        if key in {"accepted_source_evidence_packet_version"}:
            if item != EXPECTED_PACKET_VERSION:
                failures.append(f"{path} must be {EXPECTED_PACKET_VERSION}")
        if key in {"accepted_source_evidence_packet_authority_class"}:
            if item != EXPECTED_ACCEPTED_PACKET_AUTHORITY:
                failures.append(f"{path} must be {EXPECTED_ACCEPTED_PACKET_AUTHORITY}")
        if isinstance(item, str):
            upper = item.upper()
            for marker in sorted(FORBIDDEN_STRING_MARKERS):
                if marker in upper:
                    failures.append(f"{path} contains forbidden claim marker {marker}")
            if "CANDIDATE_SOURCE_PACKET" in upper and key.startswith(
                "accepted_source_evidence_packet"
            ):
                failures.append(f"{path} must not reference a candidate packet as accepted")
            if "://" in item:
                failures.append(f"{path} must not contain an external locator or URL")
    return failures


def _validate_schema(
    schema: dict[str, Any],
    *,
    schema_key: str,
    schema_path: pathlib.Path,
) -> list[str]:
    spec = SCHEMA_REQUIRED_FIELDS[schema_key]
    type_field = next(field for field in spec if field != "required")
    expected_type = spec[type_field]
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{schema_path}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path}.additionalProperties must be false")
    if _const_value(schema, type_field) != expected_type:
        failures.append(f"{schema_path}.{type_field} must be {expected_type}")
    missing_required = sorted(set(spec["required"]) - _required(schema))
    if missing_required:
        failures.append(
            f"{schema_path} missing required schema fields: {', '.join(missing_required)}"
        )
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        failures.append(f"{schema_path} missing $defs")
        return failures
    hooks = _properties(schema).get("validation_hook_ids", {})
    if isinstance(hooks, dict) and hooks.get("$ref") == "#/$defs/validation_hook_ids":
        hooks = defs.get("validation_hook_ids", {})
    hook_items = hooks.get("items", {}) if isinstance(hooks, dict) else {}
    if not isinstance(hook_items, dict) or hook_items.get("const") != VALIDATION_HOOK:
        failures.append(f"{schema_path}.validation_hook_ids must require {VALIDATION_HOOK}")
    no_claims = defs.get("no_claim_flags")
    if not isinstance(no_claims, dict):
        failures.append(f"{schema_path} missing no_claim_flags $defs entry")
    else:
        failures.extend(_validate_no_claim_schema(no_claims, str(schema_path)))
    return failures


def _validate_no_claim_schema(definition: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    properties = _properties(definition)
    required = _required(definition)
    for field, expected in sorted(NO_CLAIM_FLAGS.items()):
        prop = properties.get(field)
        if not isinstance(prop, dict):
            failures.append(f"{label}.no_claim_flags missing field {field}")
            continue
        if field not in required:
            failures.append(f"{label}.no_claim_flags must require {field}")
        if prop.get("const") is not expected:
            failures.append(f"{label}.no_claim_flags.{field} must be const {expected}")
    return failures


def _validate_common_record(record: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic data")
    if record.get("accepted_source_evidence_packet_version") != EXPECTED_PACKET_VERSION:
        failures.append(
            f"{label}.accepted_source_evidence_packet_version must be synthetic accepted reference"
        )
    if record.get("accepted_source_evidence_packet_authority_class") != (
        EXPECTED_ACCEPTED_PACKET_AUTHORITY
    ):
        failures.append(
            f"{label}.accepted_source_evidence_packet_authority_class must not be candidate authority"
        )
    if not _is_sha256(record.get("accepted_source_evidence_packet_digest")):
        failures.append(f"{label}.accepted_source_evidence_packet_digest must be sha256-like")
    if not _is_sha256(record.get("target_field_path_hash")):
        failures.append(f"{label}.target_field_path_hash must be sha256-like")
    elif record.get("target_field_path_hash") != _hash_text(record.get("target_field_path", "")):
        failures.append(f"{label}.target_field_path_hash must match target_field_path")
    if record.get("target_field_path_hash_algorithm") != (
        "SHA256_OVER_UTF8_TARGET_FIELD_PATH_IDENTIFIER_ONLY_NOT_FREEZE_AUTHORITY"
    ):
        failures.append(f"{label}.target_field_path_hash_algorithm must be identifier-only")
    if record.get("accepted_packet_current_state") not in ACCEPTED_PACKET_CURRENT_STATES:
        failures.append(f"{label}.accepted_packet_current_state is invalid")
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(_validate_scope(record, label))
    failures.extend(_validate_consumers(record, label))
    failures.extend(_validate_no_forbidden_claims(record, label))
    return failures


def _validate_scope(record: dict[str, Any], label: str) -> list[str]:
    scope = record.get("accepted_packet_applicability_scope")
    if not isinstance(scope, dict):
        return [f"{label}.accepted_packet_applicability_scope must be an object"]
    failures = _require_exact_fields(
        scope,
        {
            "scope_id",
            "scope_authority_class",
            "venue_id",
            "target_field_paths",
            "wildcard_scope_allowed",
            "cross_venue_scope_allowed",
        },
        f"{label}.accepted_packet_applicability_scope",
    )
    if scope.get("scope_authority_class") != "SYNTHETIC_SCOPE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY":
        failures.append(f"{label}.accepted_packet_applicability_scope must be synthetic")
    if scope.get("venue_id") != record.get("venue_id"):
        failures.append(f"{label}.accepted_packet_applicability_scope.venue_id must match record")
    if scope.get("wildcard_scope_allowed") is not False:
        failures.append(f"{label}.accepted_packet_applicability_scope.wildcard_scope_allowed must be false")
    if scope.get("cross_venue_scope_allowed") is not False:
        failures.append(f"{label}.accepted_packet_applicability_scope.cross_venue_scope_allowed must be false")
    paths = scope.get("target_field_paths")
    if paths != [record.get("target_field_path")]:
        failures.append(
            f"{label}.accepted_packet_applicability_scope.target_field_paths must contain only target_field_path"
        )
    if isinstance(record.get("target_field_path"), str) and "*" in record["target_field_path"]:
        failures.append(f"{label}.target_field_path must not contain wildcard")
    return failures


def _validate_consumers(record: dict[str, Any], label: str) -> list[str]:
    consumers = record.get("authorized_consumer_task_ids")
    failures: list[str] = []
    if not isinstance(consumers, list) or not consumers:
        return [f"{label}.authorized_consumer_task_ids must be a non-empty list"]
    if len(set(consumers)) != len(consumers):
        failures.append(f"{label}.authorized_consumer_task_ids must be unique")
    for consumer in consumers:
        if not isinstance(consumer, str) or not consumer:
            failures.append(f"{label}.authorized_consumer_task_ids must contain strings")
        elif "*" in consumer:
            failures.append(f"{label}.authorized_consumer_task_ids must not contain wildcards")
    return failures


def validate_target_field_ledger_record(record: dict[str, Any], *, label: str = "target ledger record") -> list[str]:
    failures = _require_exact_fields(record, LEDGER_FIELDS, label)
    if record.get("target_field_acceptance_ledger_record_type") != LEDGER_RECORD_TYPE:
        failures.append(f"{label}.target_field_acceptance_ledger_record_type must be {LEDGER_RECORD_TYPE}")
    if not _is_sha256(record.get("target_field_acceptance_ledger_record_digest")):
        failures.append(f"{label}.target_field_acceptance_ledger_record_digest must be sha256-like")
    if record.get("consumer_contract_required_flag") is not True:
        failures.append(f"{label}.consumer_contract_required_flag must be true")
    if record.get("connector_semantic_binding_allowed_directly_from_ledger_flag") is not False:
        failures.append(f"{label}.connector_semantic_binding_allowed_directly_from_ledger_flag must be false")
    failures.extend(_validate_common_record(record, label))
    return failures


def _blocking_state_for(record: dict[str, Any]) -> str | None:
    requested_consumer = record.get("requested_consumer_task_id")
    requested_target = record.get("requested_target_field_path")
    target = record.get("target_field_path")
    current_state = record.get("accepted_packet_current_state")
    conflict_state = record.get("accepted_packet_conflict_state")
    blockers = record.get("blocker_codes")

    if requested_target != target:
        return BLOCKED_TARGET_MISMATCH
    if requested_consumer not in record.get("authorized_consumer_task_ids", []):
        return BLOCKED_CONSUMER_NOT_DECLARED
    if current_state in {"STALE_REVALIDATION_REQUIRED", "SUPERSEDED"}:
        return BLOCKED_STALE
    if current_state in {"BLOCKED_CONFLICT", "BLOCKED_SCHEMA_ERROR"}:
        return BLOCKED_CONFLICT
    if conflict_state != "NO_CONFLICT":
        return BLOCKED_CONFLICT
    if isinstance(blockers, list) and blockers:
        return BLOCKED_CONFLICT
    return None


def validate_export_record(record: dict[str, Any], *, label: str = "export record") -> list[str]:
    failures = _require_exact_fields(record, EXPORT_FIELDS, label)
    if record.get("accepted_source_evidence_export_record_type") != EXPORT_RECORD_TYPE:
        failures.append(f"{label}.accepted_source_evidence_export_record_type must be {EXPORT_RECORD_TYPE}")
    if not _is_sha256(record.get("target_field_acceptance_ledger_record_digest")):
        failures.append(f"{label}.target_field_acceptance_ledger_record_digest must be sha256-like")
    if record.get("consumer_authorization_state") not in CONSUMER_AUTHORIZATION_STATES:
        failures.append(f"{label}.consumer_authorization_state is invalid")
    failures.extend(_validate_common_record(record, label))

    blocking_state = _blocking_state_for(record)
    if blocking_state is None:
        if record.get("consumer_authorization_state") != AUTHORIZED_STATE:
            failures.append(f"{label}.consumer_authorization_state must be authorized when no blocker exists")
        if record.get("connector_semantic_binding_allowed_flag") is not True:
            failures.append(f"{label}.connector_semantic_binding_allowed_flag must be true only for valid current nonlive consumption")
        if record.get("blocker_codes") != []:
            failures.append(f"{label}.blocker_codes must be empty for authorized current records")
    else:
        if record.get("consumer_authorization_state") != blocking_state:
            failures.append(
                f"{label}.consumer_authorization_state must be {blocking_state} for this blocked record"
            )
        if record.get("connector_semantic_binding_allowed_flag") is not False:
            failures.append(f"{label}.connector_semantic_binding_allowed_flag must be false when blocked")
        if not record.get("blocker_codes"):
            failures.append(f"{label}.blocker_codes must explain blocked records")
    return failures


def validate_consumer_contract_record(
    record: dict[str, Any],
    *,
    export_records_by_id: dict[str, dict[str, Any]] | None = None,
    label: str = "consumer contract record",
) -> list[str]:
    failures = _require_exact_fields(record, CONTRACT_FIELDS, label)
    if record.get("accepted_source_evidence_consumer_contract_type") != CONSUMER_CONTRACT_TYPE:
        failures.append(
            f"{label}.accepted_source_evidence_consumer_contract_type must be {CONSUMER_CONTRACT_TYPE}"
        )
    if record.get("candidate_evidence_packet_is_accepted_source_evidence_flag") is not False:
        failures.append(f"{label}.candidate_evidence_packet_is_accepted_source_evidence_flag must be false")
    if record.get("nonlive_schema_level_downstream_work_only_flag") is not True:
        failures.append(f"{label}.nonlive_schema_level_downstream_work_only_flag must be true")
    if record.get("consumer_authorization_state") not in CONSUMER_AUTHORIZATION_STATES:
        failures.append(f"{label}.consumer_authorization_state is invalid")
    failures.extend(_validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(_validate_consumers(record, label))
    failures.extend(_validate_no_forbidden_claims(record, label))

    export_record = None
    if export_records_by_id is not None:
        export_id = record.get("accepted_source_evidence_export_record_id")
        export_record = export_records_by_id.get(export_id)
        if export_record is None:
            failures.append(f"{label}.accepted_source_evidence_export_record_id must reference an export record")

    if export_record is not None:
        comparisons = {
            "target_field_acceptance_ledger_record_id",
            "source_target_id",
            "venue_id",
            "target_field_path",
            "requested_target_field_path",
            "requested_consumer_task_id",
            "accepted_packet_current_state",
            "consumer_authorization_state",
            "connector_semantic_binding_allowed_flag",
            "connector_semantic_value_population_allowed_flag",
            "runtime_resolver_snapshot_allowed_flag",
            "live_reachability_allowed_flag",
            "order_execution_allowed_flag",
            "runtime_cash_claim_allowed_flag",
            "blocker_codes",
        }
        for field in sorted(comparisons):
            if record.get(field) != export_record.get(field):
                failures.append(f"{label}.{field} must match referenced export record")
        if record.get("authorized_consumer_task_ids") != export_record.get("authorized_consumer_task_ids"):
            failures.append(f"{label}.authorized_consumer_task_ids must match referenced export record")
    else:
        blocking_state = _blocking_state_for(record)
        if blocking_state is None and record.get("consumer_authorization_state") != AUTHORIZED_STATE:
            failures.append(f"{label}.consumer_authorization_state must be authorized when no blocker exists")
        if blocking_state is not None and record.get("consumer_authorization_state") != blocking_state:
            failures.append(f"{label}.consumer_authorization_state must be {blocking_state}")
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = _require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT":
        failures.append("fixture.fixture_authority_class must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT":
        failures.append("fixture.example_authority_class must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append("fixture.synthetic_data_notice must mark synthetic data")
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(
        _validate_bool_map(
            fixture.get("fixture_no_claim_flags"),
            FIXTURE_NO_CLAIM_FLAGS,
            "fixture.fixture_no_claim_flags",
        )
    )
    failures.extend(_validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "fixture.no_claim_flags"))

    ledger_records = fixture.get("target_field_acceptance_ledger_records")
    export_records = fixture.get("accepted_source_evidence_export_records")
    contract_records = fixture.get("consumer_contract_records")
    if not isinstance(ledger_records, list) or not ledger_records:
        failures.append("fixture.target_field_acceptance_ledger_records must be a non-empty list")
        ledger_records = []
    if not isinstance(export_records, list) or not export_records:
        failures.append("fixture.accepted_source_evidence_export_records must be a non-empty list")
        export_records = []
    if not isinstance(contract_records, list) or not contract_records:
        failures.append("fixture.consumer_contract_records must be a non-empty list")
        contract_records = []

    ledger_by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(ledger_records):
        if not isinstance(record, dict):
            failures.append(f"target_field_acceptance_ledger_records[{index}] must be an object")
            continue
        failures.extend(
            validate_target_field_ledger_record(
                record,
                label=f"target_field_acceptance_ledger_records[{index}]",
            )
        )
        ledger_id = record.get("target_field_acceptance_ledger_record_id")
        if isinstance(ledger_id, str):
            ledger_by_id[ledger_id] = record

    export_by_id: dict[str, dict[str, Any]] = {}
    export_cases: set[str] = set()
    for index, record in enumerate(export_records):
        if not isinstance(record, dict):
            failures.append(f"accepted_source_evidence_export_records[{index}] must be an object")
            continue
        failures.extend(
            validate_export_record(
                record,
                label=f"accepted_source_evidence_export_records[{index}]",
            )
        )
        export_id = record.get("accepted_source_evidence_export_record_id")
        if isinstance(export_id, str):
            export_by_id[export_id] = record
        case = record.get("fixture_case")
        if isinstance(case, str):
            export_cases.add(case)
        ledger = ledger_by_id.get(record.get("target_field_acceptance_ledger_record_id"))
        if ledger is None:
            failures.append(
                f"accepted_source_evidence_export_records[{index}] must reference a ledger record"
            )
            continue
        for field in [
            "target_field_acceptance_ledger_record_digest",
            "accepted_source_evidence_packet_id",
            "accepted_source_evidence_packet_digest",
            "source_target_id",
            "venue_id",
            "target_field_path",
            "target_field_path_hash",
            "accepted_packet_current_state",
            "authorized_consumer_task_ids",
        ]:
            ledger_field = (
                "target_field_acceptance_ledger_record_digest"
                if field == "target_field_acceptance_ledger_record_digest"
                else field
            )
            if record.get(field) != ledger.get(ledger_field):
                failures.append(
                    f"accepted_source_evidence_export_records[{index}].{field} must match referenced ledger"
                )

    missing_cases = sorted(REQUIRED_FIXTURE_CASES - export_cases)
    if missing_cases:
        failures.append(f"fixture missing required fixture cases: {', '.join(missing_cases)}")

    for index, record in enumerate(contract_records):
        if not isinstance(record, dict):
            failures.append(f"consumer_contract_records[{index}] must be an object")
            continue
        failures.extend(
            validate_consumer_contract_record(
                record,
                export_records_by_id=export_by_id,
                label=f"consumer_contract_records[{index}]",
            )
        )

    failures.extend(_validate_no_forbidden_claims(fixture, "fixture"))
    failures.extend(_atomicrows_absence_failures(repo_root, "accepted source-evidence consumer contract"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    consumer_contract_schema_path: pathlib.Path = DEFAULT_CONSUMER_CONTRACT_SCHEMA,
    target_field_ledger_schema_path: pathlib.Path = DEFAULT_LEDGER_SCHEMA,
    export_record_schema_path: pathlib.Path = DEFAULT_EXPORT_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    consumer_schema, consumer_failures = _load_json(consumer_contract_schema_path)
    ledger_schema, ledger_failures = _load_json(target_field_ledger_schema_path)
    export_schema, export_failures = _load_json(export_record_schema_path)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(consumer_failures)
    failures.extend(ledger_failures)
    failures.extend(export_failures)
    failures.extend(fixture_failures)

    if consumer_schema is not None:
        failures.extend(
            _validate_schema(
                consumer_schema,
                schema_key="consumer",
                schema_path=consumer_contract_schema_path,
            )
        )
    if ledger_schema is not None:
        failures.extend(
            _validate_schema(
                ledger_schema,
                schema_key="ledger",
                schema_path=target_field_ledger_schema_path,
            )
        )
    if export_schema is not None:
        failures.extend(
            _validate_schema(
                export_schema,
                schema_key="export",
                schema_path=export_record_schema_path,
            )
        )
    if fixture is not None:
        failures.extend(validate_fixture(fixture, repo_root=repo_root))
    failures.extend(_atomicrows_absence_failures(repo_root, "PR39 consumer contract validator"))
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--consumer-contract-schema",
        default=str(DEFAULT_CONSUMER_CONTRACT_SCHEMA),
    )
    parser.add_argument(
        "--target-field-ledger-schema",
        default=str(DEFAULT_LEDGER_SCHEMA),
    )
    parser.add_argument(
        "--export-record-schema",
        default=str(DEFAULT_EXPORT_SCHEMA),
    )
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    failures = validate_static_surface(
        repo_root=pathlib.Path(args.repo_root),
        consumer_contract_schema_path=pathlib.Path(args.consumer_contract_schema),
        target_field_ledger_schema_path=pathlib.Path(args.target_field_ledger_schema),
        export_record_schema_path=pathlib.Path(args.export_record_schema),
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
