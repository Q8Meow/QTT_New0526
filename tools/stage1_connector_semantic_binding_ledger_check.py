#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any, Iterable, Sequence

try:
    from stage1_connector_semantic_value_canonicalize import (
        ACCEPTED_SOURCE_ORIGIN,
        CANONICAL_ATOMICROWS_BUNDLE,
        CANONICAL_ATOMICROWS_BUNDLE_SHA,
        EXPECTED_SYNTHETIC_NOTICE,
        NO_CLAIM_FLAGS,
        VALIDATION_HOOK,
        VALID_CANONICALIZATION_STATE,
        canonical_atomicrows_absence_failures,
        load_json_object,
        missing_reference,
        require_exact_fields,
        validate_bool_map,
        validate_canonicalization_record,
        validate_no_forbidden_claims,
    )
except ModuleNotFoundError:
    from tools.stage1_connector_semantic_value_canonicalize import (
        ACCEPTED_SOURCE_ORIGIN,
        CANONICAL_ATOMICROWS_BUNDLE,
        CANONICAL_ATOMICROWS_BUNDLE_SHA,
        EXPECTED_SYNTHETIC_NOTICE,
        NO_CLAIM_FLAGS,
        VALIDATION_HOOK,
        VALID_CANONICALIZATION_STATE,
        canonical_atomicrows_absence_failures,
        load_json_object,
        missing_reference,
        require_exact_fields,
        validate_bool_map,
        validate_canonicalization_record,
        validate_no_forbidden_claims,
    )

SUCCESS_MARKER = "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_OK"
FAILURE_MARKER = "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_FAILED"

LEDGER_RECORD_TYPE = "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_RECORD"
CANONICALIZATION_TYPE = "STAGE1_CONNECTOR_SEMANTIC_VALUE_CANONICALIZATION"
CONSUMER_CONTRACT_TYPE = "STAGE1_CONNECTOR_SEMANTIC_BINDING_CONSUMER_CONTRACT"
REPORT_TYPE = "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_REPORT"

CONSUMABLE_STATE = "CONSUMABLE_BY_RUNTIME_RESOLVER_GATE_ONLY"
BLOCKED_STALE = "BLOCKED_STALE"
BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
BLOCKED_TARGET_MISMATCH = "BLOCKED_TARGET_MISMATCH"
BLOCKED_SCHEMA_ERROR = "BLOCKED_SCHEMA_ERROR"

DEFAULT_LEDGER_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_ledger_record.schema.json"
)
DEFAULT_CANONICALIZATION_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_value_canonicalization.schema.json"
)
DEFAULT_CONSUMER_CONTRACT_SCHEMA = pathlib.Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_consumer_contract.schema.json"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/connector_semantic_binding/"
    "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
)
DEFAULT_MASTER_PLAN = pathlib.Path("docs/master_plan/QTT_MasterPlan_Current.md")

REQUIRED_FIXTURE_CASES = {
    "VALID_SYNTHETIC_BINDING_NONLIVE_ONLY",
    "BLOCKED_STALE_BINDING",
    "BLOCKED_CONFLICT_BINDING",
    "BLOCKED_TARGET_MISMATCH_BINDING",
    "BLOCKED_SCHEMA_ERROR_BINDING",
    "BLOCKED_MISSING_ACCEPTED_SOURCE_EXPORT_RECORD",
    "BLOCKED_MISSING_TARGET_FIELD_ACCEPTANCE_LEDGER_RECORD",
    "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_BINDING_RECORD",
    "BLOCKED_ZERO_FILL_INVENTED_MISSING_VALUE_ATTEMPT",
    "BLOCKED_OWNER_POLICY_SUBSTITUTION_ATTEMPT",
    "BLOCKED_RUNTIME_OBSERVED_VALUE_SUBSTITUTION_ATTEMPT",
    "BLOCKED_LIVE_CLIENT_NETWORK_ORDER_REACHABILITY_CLAIM_ATTEMPT",
}

LEDGER_RECORD_FIELDS = {
    "connector_semantic_binding_ledger_record_type",
    "connector_semantic_binding_ledger_record_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "binding_packet_id",
    "binding_manifest_id",
    "accepted_source_evidence_export_record_id",
    "accepted_source_evidence_packet_id",
    "accepted_source_evidence_packet_digest",
    "accepted_source_evidence_packet_version",
    "accepted_source_evidence_packet_authority_class",
    "target_field_acceptance_ledger_record_id",
    "target_field_acceptance_ledger_record_digest",
    "source_to_connector_field_binding_record_id",
    "semantic_value_canonicalization_record_id",
    "venue_id",
    "canonical_connector_namespace",
    "semantic_surface_id",
    "target_field_path",
    "bound_value_original",
    "bound_value_canonical",
    "bound_value_type",
    "bound_value_unit_or_scale",
    "bound_value_normalization_rule_id",
    "bound_value_rounding_or_precision_rule_id_when_applicable",
    "bound_value_scope",
    "source_value_origin",
    "source_value_required_flag",
    "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
    "revalidation_due_condition",
    "stale_binding_invalidates_downstream_snapshot_flag",
    "rollback_receipt_required_flag",
    "consumer_contract_state",
    "binding_packet_creation_allowed_flag",
    "production_connector_semantic_value_population_allowed_flag",
    "production_connector_semantic_authority",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "replay_paper_consumption_allowed_without_runtime_resolver_snapshot_input_lock_flag",
    "live_client_import_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "receipt_ids",
    "blocker_codes",
    "no_claim_flags",
    "validation_hook_ids",
}

CONSUMER_CONTRACT_FIELDS = {
    "stage1_connector_semantic_binding_consumer_contract_type",
    "stage1_connector_semantic_binding_consumer_contract_id",
    "fixture_case",
    "contract_authority_class",
    "synthetic_data_notice",
    "consumer_id",
    "consumer_class",
    "ledger_consumption_authorization_state",
    "runtime_resolver_gate_may_consume_connector_semantic_binding_ledger_as_gate_input_only_flag",
    "runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green_flag",
    "venue_connector_scaffold_static_non_live_configuration_tests_only_flag",
    "venue_connector_live_client_may_consume_binding_flag",
    "replay_paper_may_consume_without_runtime_resolver_snapshot_input_lock_flag",
    "connector_semantic_binding_ledger_is_live_order_authority_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "direct_runtime_use_allowed_flag",
    "live_client_import_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "replay_paper_live_order_profit_claim_allowed_flag",
    "runtime_resolver_snapshot_input_lock_required_before_replay_paper_flag",
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
    "connector_semantic_binding_ledger_records",
    "semantic_value_canonicalization_records",
    "consumer_contract_records",
}

SCHEMA_REQUIRED_FIELDS = {
    "ledger": {
        "type_field": "connector_semantic_binding_ledger_record_type",
        "type_value": LEDGER_RECORD_TYPE,
        "required": LEDGER_RECORD_FIELDS,
    },
    "canonicalization": {
        "type_field": "stage1_connector_semantic_value_canonicalization_type",
        "type_value": CANONICALIZATION_TYPE,
        "required": {
            "stage1_connector_semantic_value_canonicalization_type",
            "semantic_value_canonicalization_record_id",
            "fixture_case",
            "synthetic_data_notice",
            "accepted_source_evidence_export_record_id",
            "target_field_acceptance_ledger_record_id",
            "source_to_connector_field_binding_record_id",
            "target_field_path",
            "bound_value_original",
            "bound_value_canonical",
            "bound_value_type",
            "bound_value_unit_or_scale",
            "bound_value_scope",
            "source_value_origin",
            "canonicalization_state",
            "binding_packet_creation_allowed_flag",
            "blocker_codes",
            "receipt_ids",
            "no_claim_flags",
            "validation_hook_ids",
        },
    },
    "consumer": {
        "type_field": "stage1_connector_semantic_binding_consumer_contract_type",
        "type_value": CONSUMER_CONTRACT_TYPE,
        "required": CONSUMER_CONTRACT_FIELDS,
    },
}


def _properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _required(schema: dict[str, Any]) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _const_value(schema: dict[str, Any], field: str) -> Any:
    prop = _properties(schema).get(field, {})
    return prop.get("const") if isinstance(prop, dict) else None


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _schema_validation_hook(schema: dict[str, Any]) -> str | None:
    defs = schema.get("$defs", {})
    if not isinstance(defs, dict):
        return None
    hooks = _properties(schema).get("validation_hook_ids", {})
    if isinstance(hooks, dict) and hooks.get("$ref") == "#/$defs/validation_hook_ids":
        hooks = defs.get("validation_hook_ids", {})
    items = hooks.get("items") if isinstance(hooks, dict) else None
    return items.get("const") if isinstance(items, dict) else None


def validate_schema(schema: dict[str, Any], *, schema_key: str, schema_path: pathlib.Path) -> list[str]:
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
    if not isinstance(schema.get("$defs"), dict):
        failures.append(f"{schema_path} missing $defs")
    if _schema_validation_hook(schema) != VALIDATION_HOOK:
        failures.append(f"{schema_path}.validation_hook_ids must require {VALIDATION_HOOK}")
    return failures


def _validate_scope(record: dict[str, Any], label: str) -> list[str]:
    scope = record.get("bound_value_scope")
    if not isinstance(scope, dict):
        return [f"{label}.bound_value_scope must be an object"]
    failures = require_exact_fields(
        scope,
        {
            "scope_id",
            "scope_authority_class",
            "venue_id",
            "target_field_path",
            "wildcard_scope_allowed",
            "cross_venue_scope_allowed",
        },
        f"{label}.bound_value_scope",
    )
    if scope.get("scope_authority_class") != "SYNTHETIC_SCOPE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY":
        failures.append(f"{label}.bound_value_scope.scope_authority_class must be synthetic")
    if scope.get("venue_id") != record.get("venue_id"):
        failures.append(f"{label}.bound_value_scope.venue_id must match record")
    if scope.get("target_field_path") != record.get("target_field_path"):
        failures.append(f"{label}.bound_value_scope.target_field_path must match record")
    if scope.get("wildcard_scope_allowed") is not False:
        failures.append(f"{label}.bound_value_scope.wildcard_scope_allowed must be false")
    if scope.get("cross_venue_scope_allowed") is not False:
        failures.append(f"{label}.bound_value_scope.cross_venue_scope_allowed must be false")
    return failures


def _expected_consumer_state_for_case(fixture_case: str) -> str | None:
    if fixture_case == "VALID_SYNTHETIC_BINDING_NONLIVE_ONLY":
        return CONSUMABLE_STATE
    if fixture_case == "BLOCKED_STALE_BINDING":
        return BLOCKED_STALE
    if fixture_case == "BLOCKED_CONFLICT_BINDING":
        return BLOCKED_CONFLICT
    if fixture_case == "BLOCKED_TARGET_MISMATCH_BINDING":
        return BLOCKED_TARGET_MISMATCH
    if fixture_case in REQUIRED_FIXTURE_CASES:
        return BLOCKED_SCHEMA_ERROR
    return None


def validate_ledger_record(
    record: dict[str, Any],
    *,
    canonicalization_records_by_id: dict[str, dict[str, Any]] | None = None,
    label: str = "ledger record",
) -> list[str]:
    failures = require_exact_fields(record, LEDGER_RECORD_FIELDS, label)
    if record.get("connector_semantic_binding_ledger_record_type") != LEDGER_RECORD_TYPE:
        failures.append(
            f"{label}.connector_semantic_binding_ledger_record_type must be {LEDGER_RECORD_TYPE}"
        )
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if not _is_sha256(record.get("accepted_source_evidence_packet_digest")):
        failures.append(f"{label}.accepted_source_evidence_packet_digest must be sha256-like")
    if not _is_sha256(record.get("target_field_acceptance_ledger_record_digest")):
        failures.append(f"{label}.target_field_acceptance_ledger_record_digest must be sha256-like")
    if record.get("source_value_required_flag") is not True:
        failures.append(f"{label}.source_value_required_flag must be true")
    if record.get("stale_binding_invalidates_downstream_snapshot_flag") is not True:
        failures.append(f"{label}.stale_binding_invalidates_downstream_snapshot_flag must be true")
    if record.get("rollback_receipt_required_flag") is not True:
        failures.append(f"{label}.rollback_receipt_required_flag must be true")
    for field in [
        "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
        "production_connector_semantic_value_population_allowed_flag",
        "production_connector_semantic_authority",
        "runtime_resolver_snapshot_creation_allowed_flag",
        "replay_paper_consumption_allowed_without_runtime_resolver_snapshot_input_lock_flag",
        "live_client_import_allowed_flag",
        "network_io_allowed_flag",
        "order_execution_allowed_flag",
        "live_reachability_allowed_flag",
    ]:
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(_validate_scope(record, label))
    failures.extend(validate_no_forbidden_claims(record, label))

    fixture_case = record.get("fixture_case")
    expected_state = _expected_consumer_state_for_case(fixture_case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR40 fixture case")
    elif record.get("consumer_contract_state") != expected_state:
        failures.append(
            f"{label}.consumer_contract_state must be {expected_state} for {fixture_case}"
        )

    blockers = record.get("blocker_codes")
    if not isinstance(blockers, list):
        failures.append(f"{label}.blocker_codes must be a list")
        blockers = []
    if not isinstance(record.get("receipt_ids"), list) or not record.get("receipt_ids"):
        failures.append(f"{label}.receipt_ids must be a non-empty list")

    link_fields = [
        "accepted_source_evidence_export_record_id",
        "target_field_acceptance_ledger_record_id",
        "source_to_connector_field_binding_record_id",
    ]
    has_missing_link = any(missing_reference(record.get(field)) for field in link_fields)
    is_consumable = record.get("consumer_contract_state") == CONSUMABLE_STATE
    if is_consumable:
        if record.get("binding_packet_creation_allowed_flag") is not True:
            failures.append(f"{label}.binding_packet_creation_allowed_flag must be true when consumable")
        if blockers:
            failures.append(f"{label}.blocker_codes must be empty when consumable")
        if has_missing_link:
            failures.append(f"{label} consumable records require all linkage records")
        if record.get("source_value_origin") != ACCEPTED_SOURCE_ORIGIN:
            failures.append(f"{label}.source_value_origin must be {ACCEPTED_SOURCE_ORIGIN}")
        if record.get("revalidation_due_condition") != "NOT_DUE_SYNTHETIC_CURRENT":
            failures.append(f"{label}.revalidation_due_condition must not be due when consumable")
    else:
        if record.get("binding_packet_creation_allowed_flag") is not False:
            failures.append(f"{label}.binding_packet_creation_allowed_flag must be false when blocked")
        if not blockers:
            failures.append(f"{label}.blocker_codes must explain blocked records")

    canonicalization_record = None
    if canonicalization_records_by_id is not None:
        canonicalization_id = record.get("semantic_value_canonicalization_record_id")
        canonicalization_record = canonicalization_records_by_id.get(canonicalization_id)
        if canonicalization_record is None:
            failures.append(f"{label}.semantic_value_canonicalization_record_id must reference a record")
    if canonicalization_record is not None:
        comparisons = {
            "accepted_source_evidence_export_record_id",
            "target_field_acceptance_ledger_record_id",
            "source_to_connector_field_binding_record_id",
            "target_field_path",
            "bound_value_original",
            "bound_value_canonical",
            "bound_value_type",
            "bound_value_unit_or_scale",
            "bound_value_normalization_rule_id",
            "bound_value_rounding_or_precision_rule_id_when_applicable",
            "source_value_origin",
        }
        for field in sorted(comparisons):
            if record.get(field) != canonicalization_record.get(field):
                failures.append(f"{label}.{field} must match referenced canonicalization record")
        if canonicalization_record.get("canonicalization_state") != VALID_CANONICALIZATION_STATE and is_consumable:
            failures.append(f"{label} cannot be consumable when canonicalization is blocked")
    return failures


def validate_consumer_contract_record(record: dict[str, Any], *, label: str = "consumer contract record") -> list[str]:
    failures = require_exact_fields(record, CONSUMER_CONTRACT_FIELDS, label)
    if record.get("stage1_connector_semantic_binding_consumer_contract_type") != CONSUMER_CONTRACT_TYPE:
        failures.append(
            f"{label}.stage1_connector_semantic_binding_consumer_contract_type must be {CONSUMER_CONTRACT_TYPE}"
        )
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    for field, expected in {
        "runtime_resolver_gate_may_consume_connector_semantic_binding_ledger_as_gate_input_only_flag": True,
        "runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green_flag": True,
        "venue_connector_scaffold_static_non_live_configuration_tests_only_flag": True,
        "venue_connector_live_client_may_consume_binding_flag": False,
        "replay_paper_may_consume_without_runtime_resolver_snapshot_input_lock_flag": False,
        "connector_semantic_binding_ledger_is_live_order_authority_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
        "direct_runtime_use_allowed_flag": False,
        "live_client_import_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
        "replay_paper_live_order_profit_claim_allowed_flag": False,
        "runtime_resolver_snapshot_input_lock_required_before_replay_paper_flag": True,
    }.items():
        if record.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(validate_no_forbidden_claims(record, label))

    expected_state_by_consumer_class = {
        "RUNTIME_RESOLVER_GATE_ONLY": "AUTHORIZED_GATE_INPUT_ONLY",
        "VENUE_CONNECTOR_SCAFFOLD_STATIC_TEST_ONLY": "AUTHORIZED_GATE_INPUT_ONLY",
        "RUNTIME_RESOLVER_SNAPSHOT_CREATE_DIRECT": "BLOCKED_DIRECT_RUNTIME_USE",
        "VENUE_CONNECTOR_LIVE_CLIENT": "BLOCKED_LIVE_CLIENT",
        "REPLAY_PAPER_WITHOUT_RUNTIME_RESOLVER_INPUT_LOCK": "BLOCKED_REPLAY_PAPER_WITHOUT_INPUT_LOCK",
        "LIVE_ORDER_AUTHORITY_ATTEMPT": "BLOCKED_LIVE_ORDER_AUTHORITY",
    }
    expected_state = expected_state_by_consumer_class.get(record.get("consumer_class"))
    if expected_state is None:
        failures.append(f"{label}.consumer_class is invalid")
    elif record.get("ledger_consumption_authorization_state") != expected_state:
        failures.append(
            f"{label}.ledger_consumption_authorization_state must be {expected_state}"
        )
    blockers = record.get("blocker_codes")
    if not isinstance(blockers, list):
        failures.append(f"{label}.blocker_codes must be a list")
    elif expected_state == "AUTHORIZED_GATE_INPUT_ONLY" and blockers:
        failures.append(f"{label}.blocker_codes must be empty for gate-only/static-test consumers")
    elif expected_state != "AUTHORIZED_GATE_INPUT_ONLY" and not blockers:
        failures.append(f"{label}.blocker_codes must explain blocked consumers")
    if not isinstance(record.get("receipt_ids"), list) or not record.get("receipt_ids"):
        failures.append(f"{label}.receipt_ids must be a non-empty list")
    return failures


def validate_fixture(fixture: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT"
    ):
        failures.append("fixture.fixture_authority_class must be synthetic non-authority")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_CONNECTOR_SEMANTIC_AUTHORITY"
    ):
        failures.append("fixture.example_authority_class must be synthetic non-authority")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append("fixture.synthetic_data_notice must mark synthetic non-authority")
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    fixture_no_claim_flags = {"retrieves_source_facts": False, **NO_CLAIM_FLAGS}
    failures.extend(
        validate_bool_map(
            fixture.get("fixture_no_claim_flags"),
            fixture_no_claim_flags,
            "fixture.fixture_no_claim_flags",
        )
    )
    failures.extend(validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "fixture.no_claim_flags"))
    failures.extend(validate_no_forbidden_claims(fixture, "fixture"))

    canonicalization_records = fixture.get("semantic_value_canonicalization_records")
    ledger_records = fixture.get("connector_semantic_binding_ledger_records")
    consumer_records = fixture.get("consumer_contract_records")
    if not isinstance(canonicalization_records, list) or not canonicalization_records:
        failures.append("fixture.semantic_value_canonicalization_records must be a non-empty list")
        canonicalization_records = []
    if not isinstance(ledger_records, list) or not ledger_records:
        failures.append("fixture.connector_semantic_binding_ledger_records must be a non-empty list")
        ledger_records = []
    if not isinstance(consumer_records, list) or not consumer_records:
        failures.append("fixture.consumer_contract_records must be a non-empty list")
        consumer_records = []

    canonicalization_by_id: dict[str, dict[str, Any]] = {}
    canonicalization_cases: set[str] = set()
    for index, record in enumerate(canonicalization_records):
        if not isinstance(record, dict):
            failures.append(f"semantic_value_canonicalization_records[{index}] must be an object")
            continue
        failures.extend(
            validate_canonicalization_record(
                record,
                label=f"semantic_value_canonicalization_records[{index}]",
            )
        )
        record_id = record.get("semantic_value_canonicalization_record_id")
        if isinstance(record_id, str):
            canonicalization_by_id[record_id] = record
        case = record.get("fixture_case")
        if isinstance(case, str):
            canonicalization_cases.add(case)

    ledger_cases: set[str] = set()
    for index, record in enumerate(ledger_records):
        if not isinstance(record, dict):
            failures.append(f"connector_semantic_binding_ledger_records[{index}] must be an object")
            continue
        failures.extend(
            validate_ledger_record(
                record,
                canonicalization_records_by_id=canonicalization_by_id,
                label=f"connector_semantic_binding_ledger_records[{index}]",
            )
        )
        case = record.get("fixture_case")
        if isinstance(case, str):
            ledger_cases.add(case)

    missing_ledger_cases = sorted(REQUIRED_FIXTURE_CASES - ledger_cases)
    if missing_ledger_cases:
        failures.append(f"fixture missing required ledger fixture cases: {', '.join(missing_ledger_cases)}")
    missing_canonicalization_cases = sorted(REQUIRED_FIXTURE_CASES - canonicalization_cases)
    if missing_canonicalization_cases:
        failures.append(
            "fixture missing required canonicalization fixture cases: "
            + ", ".join(missing_canonicalization_cases)
        )

    for index, record in enumerate(consumer_records):
        if not isinstance(record, dict):
            failures.append(f"consumer_contract_records[{index}] must be an object")
            continue
        failures.extend(
            validate_consumer_contract_record(
                record,
                label=f"consumer_contract_records[{index}]",
            )
        )
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "connector semantic binding fixture"))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    ledger_schema_path: pathlib.Path = DEFAULT_LEDGER_SCHEMA,
    canonicalization_schema_path: pathlib.Path = DEFAULT_CANONICALIZATION_SCHEMA,
    consumer_contract_schema_path: pathlib.Path = DEFAULT_CONSUMER_CONTRACT_SCHEMA,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
) -> list[str]:
    failures: list[str] = []
    ledger_schema, ledger_schema_failures = load_json_object(ledger_schema_path)
    canonicalization_schema, canonicalization_schema_failures = load_json_object(
        canonicalization_schema_path
    )
    consumer_schema, consumer_schema_failures = load_json_object(consumer_contract_schema_path)
    fixture, fixture_failures = load_json_object(fixture_path)
    failures.extend(ledger_schema_failures)
    failures.extend(canonicalization_schema_failures)
    failures.extend(consumer_schema_failures)
    failures.extend(fixture_failures)
    if ledger_schema is not None:
        failures.extend(validate_schema(ledger_schema, schema_key="ledger", schema_path=ledger_schema_path))
    if canonicalization_schema is not None:
        failures.extend(
            validate_schema(
                canonicalization_schema,
                schema_key="canonicalization",
                schema_path=canonicalization_schema_path,
            )
        )
    if consumer_schema is not None:
        failures.extend(validate_schema(consumer_schema, schema_key="consumer", schema_path=consumer_contract_schema_path))
    if fixture is not None:
        failures.extend(validate_fixture(fixture, repo_root=repo_root))
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "PR40 connector semantic binding validator"))
    return failures


def _load_optional_existing_json(path_text: str | None, label: str) -> list[str]:
    if path_text is None:
        return []
    path = pathlib.Path(path_text)
    if not path.exists():
        return [f"{label} is missing: {path}"]
    _value, failures = load_json_object(path)
    return failures


def _master_plan_sha256(master_plan_path: pathlib.Path) -> str:
    if not master_plan_path.exists():
        return "MASTER_PLAN_MISSING_NO_SHA_AUTHORITY"
    import hashlib

    return hashlib.sha256(master_plan_path.read_bytes()).hexdigest()


def build_report(
    *,
    fixture: dict[str, Any] | None,
    repo_root: pathlib.Path,
    validation_failures: Sequence[str],
    master_plan_path: pathlib.Path = DEFAULT_MASTER_PLAN,
) -> dict[str, Any]:
    ledger_records = []
    canonicalization_records = []
    consumer_records = []
    if fixture is not None:
        ledger_records = fixture.get("connector_semantic_binding_ledger_records") or []
        canonicalization_records = fixture.get("semantic_value_canonicalization_records") or []
        consumer_records = fixture.get("consumer_contract_records") or []
    canonicalization_success_count = sum(
        1
        for record in canonicalization_records
        if isinstance(record, dict)
        and record.get("canonicalization_state") == VALID_CANONICALIZATION_STATE
    )
    canonicalization_failure_count = sum(
        1
        for record in canonicalization_records
        if isinstance(record, dict)
        and record.get("canonicalization_state") != VALID_CANONICALIZATION_STATE
    )
    accepted_export_missing_count = sum(
        1
        for record in ledger_records
        if isinstance(record, dict)
        and missing_reference(record.get("accepted_source_evidence_export_record_id"))
    )
    target_field_missing_count = sum(
        1
        for record in ledger_records
        if isinstance(record, dict)
        and missing_reference(record.get("target_field_acceptance_ledger_record_id"))
    )
    source_to_connector_missing_count = sum(
        1
        for record in ledger_records
        if isinstance(record, dict)
        and missing_reference(record.get("source_to_connector_field_binding_record_id"))
    )
    stale_count = sum(
        1
        for record in ledger_records
        if isinstance(record, dict) and record.get("consumer_contract_state") == BLOCKED_STALE
    )
    consumer_block_count = sum(
        1
        for record in ledger_records
        if isinstance(record, dict) and record.get("consumer_contract_state") != CONSUMABLE_STATE
    ) + sum(
        1
        for record in consumer_records
        if isinstance(record, dict)
        and record.get("ledger_consumption_authorization_state") != "AUTHORIZED_GATE_INPUT_ONLY"
    )

    def _flag_count(field: str) -> int:
        return sum(
            1
            for group in [ledger_records, consumer_records]
            for record in group
            if isinstance(record, dict) and record.get(field) is True
        )

    blocker_codes = sorted(
        {
            blocker
            for group in [ledger_records, canonicalization_records, consumer_records]
            for record in group
            if isinstance(record, dict)
            for blocker in record.get("blocker_codes", [])
            if isinstance(blocker, str)
        }
    )
    receipt_ids = sorted(
        {
            receipt
            for group in [ledger_records, canonicalization_records, consumer_records]
            for record in group
            if isinstance(record, dict)
            for receipt in record.get("receipt_ids", [])
            if isinstance(receipt, str)
        }
    )
    report = {
        "report_type": REPORT_TYPE,
        "master_plan_edition": "v9.9.742",
        "master_plan_sha256": _master_plan_sha256(repo_root / master_plan_path),
        "created_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "binding_ledger_record_count": len(ledger_records),
        "canonicalization_success_count": canonicalization_success_count,
        "canonicalization_failure_count": canonicalization_failure_count,
        "accepted_export_record_missing_count": accepted_export_missing_count,
        "target_field_ledger_record_missing_count": target_field_missing_count,
        "source_to_connector_binding_record_missing_count": source_to_connector_missing_count,
        "stale_binding_count": stale_count,
        "consumer_contract_block_count": consumer_block_count,
        "forbidden_live_client_import_count": _flag_count("live_client_import_allowed_flag"),
        "network_io_violation_count": _flag_count("network_io_allowed_flag"),
        "order_execution_violation_count": _flag_count("order_execution_allowed_flag"),
        "live_reachability_violation_count": _flag_count("live_reachability_allowed_flag"),
        "runtime_snapshot_direct_creation_violation_count": _flag_count(
            "runtime_resolver_snapshot_creation_allowed_flag"
        ),
        "gate_state": "FAIL" if validation_failures else "BLOCKED",
        "blocker_codes": blocker_codes,
        "receipt_ids_emitted": receipt_ids,
    }
    if not validation_failures and not blocker_codes:
        report["gate_state"] = "PASS"
    return report


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--ledger-schema", default=str(DEFAULT_LEDGER_SCHEMA))
    parser.add_argument("--canonicalization-schema", default=str(DEFAULT_CANONICALIZATION_SCHEMA))
    parser.add_argument("--consumer-contract-schema", default=str(DEFAULT_CONSUMER_CONTRACT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--binding-ledger")
    parser.add_argument("--accepted-consumer-contract")
    parser.add_argument("--readiness-gate")
    parser.add_argument("--out")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = pathlib.Path(args.repo_root)
    fixture_path = pathlib.Path(args.binding_ledger) if args.binding_ledger else pathlib.Path(args.fixture)
    fixture, fixture_load_failures = load_json_object(fixture_path)
    failures = validate_static_surface(
        repo_root=repo_root,
        ledger_schema_path=pathlib.Path(args.ledger_schema),
        canonicalization_schema_path=pathlib.Path(args.canonicalization_schema),
        consumer_contract_schema_path=pathlib.Path(args.consumer_contract_schema),
        fixture_path=fixture_path,
    )
    failures.extend(fixture_load_failures)
    failures.extend(
        _load_optional_existing_json(
            args.accepted_consumer_contract,
            "accepted source-evidence consumer contract report",
        )
    )
    failures.extend(
        _load_optional_existing_json(args.readiness_gate, "connector semantic readiness gate report")
    )
    report = build_report(fixture=fixture, repo_root=repo_root, validation_failures=failures)
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
