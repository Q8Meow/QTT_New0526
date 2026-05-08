#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

PACKET_VERSION_MARKER = (
    "packet_version = "
    "v1.3A_OWNER_APPROVED_EXECUTION_MECHANICS_ABSTRACTION_AND_RETRIEVAL_READINESS_CURRENTIZATION_NOT_EXTERNAL_FACT_AUTHORITY"
)
EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER = (
    "owner_source_evidence_definitions_packet_can_authorize_external_fact_value = false"
)
CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER = (
    "owner_source_evidence_definitions_packet_can_populate_connector_semantic_value = false"
)
PACKET_RETRIEVES_NO_FACTS_MARKER = "this_packet_retrieves_source_facts = false"
PACKET_ACCEPTS_NO_FACTS_MARKER = "this_packet_accepts_source_facts = false"

REQUIRED_SURFACE_DEFS = {
    "candidate_source_packet": {
        "packet_type",
        "packet_id",
        "schema_authority_class",
        "candidate_state",
        "source_target_id",
        "venue_id",
        "target_semantic_family",
        "target_field_paths",
        "source_locator_status",
        "authority_class_required",
        "expected_capture_type",
        "applicability_scope",
        "conflict_metadata",
        "materiality_metadata",
        "revalidation_metadata",
        "no_claim_flags",
        "candidate_packet_may_unlock_connector_semantics",
    },
    "accepted_source_packet": {
        "packet_type",
        "packet_id",
        "schema_authority_class",
        "candidate_packet_id",
        "acceptance_decision_packet_id",
        "retrieval_manifest_id",
        "source_target_id",
        "venue_id",
        "source_locator",
        "source_locator_type",
        "raw_capture_digest_sha256",
        "canonical_text_digest_sha256",
        "quote_span_or_machine_field_locator",
        "extracted_fact_payload",
        "extracted_fact_type",
        "target_field_paths_authorized",
        "applicability_scope",
        "acceptance_state",
        "conflict_metadata",
        "materiality_metadata",
        "revalidation_metadata",
        "receipt_ids",
        "no_connector_semantic_population_flag",
        "no_live_reachability_flag",
        "no_order_execution_flag",
        "no_runtime_cash_claim_flag",
        "no_blocker_reduction_or_profit_claim_flag",
        "no_claim_flags",
    },
    "target_field_ledger_record": {
        "record_type",
        "ledger_record_id",
        "accepted_source_packet_id",
        "accepted_source_packet_digest_sha256",
        "source_target_id",
        "venue_id",
        "target_field_path",
        "target_semantic_family",
        "applicability_scope_digest",
        "accepted_fact_payload_digest_sha256",
        "acceptance_state",
        "conflict_resolution_state",
        "revalidation_trigger",
        "revalidation_due_at_or_event",
        "ledger_record_state",
        "connector_semantic_binding_allowed_flag",
        "blocked_reason_when_not_bindable",
        "validation_hook_ids",
        "receipt_ids",
        "no_claim_flags",
    },
    "source_evidence_acceptance_registry": {
        "registry_type",
        "registry_id",
        "registry_authority_class",
        "mode",
        "execution",
        "deterministic_output",
        "registry_authority_scope_flags",
        "registry_forbidden_action_flags",
        "candidate_records",
        "accepted_records",
        "validation_hook_ids",
        "no_claim_flags",
    },
    "registry_candidate_source_evidence_record": {
        "record_type",
        "record_id",
        "candidate_source_packet_id",
        "source_target_id",
        "venue_id",
        "target_semantic_family",
        "target_field_paths",
        "candidate_state",
        "source_locator_status",
        "accepted_fact_claim_present",
        "accepted_source_packet_authority_present",
        "no_claim_flags",
        "registry_forbidden_action_flags",
    },
    "registry_accepted_source_evidence_record": {
        "record_type",
        "record_id",
        "accepted_source_packet_id",
        "accepted_source_packet_digest_sha256",
        "source_target_id",
        "venue_id",
        "target_field_path",
        "target_semantic_family",
        "accepted_record_state",
        "accepted_source_packet_authority_present",
        "accepted_fact_claim_present",
        "target_field_ledger_record_id",
        "target_field_ledger_record_state",
        "connector_semantic_binding_allowed_flag",
        "no_claim_flags",
        "registry_forbidden_action_flags",
    },
    "registry_authority_scope_flags": {
        "source_required",
        "execution_disabled",
        "candidate_records_are_not_accepted_source_evidence",
        "accepted_records_are_schema_only_without_external_fact_authority_flag",
        "accepted_fact_claims_require_accepted_source_packet_authority_flag",
        "accepted_source_packet_authority_required_before_ledger_current",
        "target_field_scope_required",
        "wildcard_scope_allowed",
        "connector_semantic_binding_allowed",
        "runtime_use_allowed",
    },
    "registry_forbidden_action_flags": {
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "runtime_enabled",
        "live_enabled",
        "private_state_fetch_enabled",
        "balance_fetch_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "atomicrows_bundle_creation_enabled",
        "sha_freeze_enabled",
    },
    "conflict_metadata": {
        "conflict_check_state",
        "conflict_resolution_state",
        "conflicting_packet_ids",
        "owner_or_risk_review_required",
        "exact_locator_quote_digest_fact_scope_target_and_revalidation_required",
        "block_code_when_unresolved",
    },
    "materiality_metadata": {
        "source_change_materiality_class",
        "affected_target_field_paths",
        "materiality_unknown_defaults_to_connector_blocking_flag",
        "owner_or_risk_review_required",
        "new_binding_blocked_when_material",
        "live_exposure_increase_blocked_when_live_trading_blocking",
    },
    "revalidation_metadata": {
        "revalidation_class",
        "revalidation_trigger",
        "revalidation_interval",
        "revalidation_due_at_or_event",
        "source_change_event_trigger_required",
        "stale_or_superseded_packet_blocks_new_connector_binding",
        "fresh_revalidation_state_required_before_new_connector_binding",
    },
    "no_claim_flags": {
        "external_fact_authority",
        "source_retrieval_authority",
        "source_acceptance_execution_authority",
        "accepted_packet_creation_authority",
        "connector_binding_authority",
        "runtime_authority",
        "runtime_cash_fetch_authority",
        "private_state_fetch_authority",
        "order_execution_authority",
        "replay_paper_live_execution_authority",
        "network_io_authority",
        "sha_freeze_authority",
        "profit_claim_authority",
    },
}

FORBIDDEN_AUTHORITY_FIELDS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "runtime_authority",
    "runtime_cash_fetch_authority",
    "private_state_fetch_authority",
    "order_execution_authority",
    "replay_paper_live_execution_authority",
    "network_io_authority",
    "sha_freeze_authority",
    "profit_claim_authority",
}

REQUIRED_TRUE_NO_RUNTIME_FLAGS = {
    "no_connector_semantic_population_flag",
    "no_live_reachability_flag",
    "no_order_execution_flag",
    "no_runtime_cash_claim_flag",
    "no_blocker_reduction_or_profit_claim_flag",
}

REGISTRY_FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_acceptance_execution_enabled",
    "external_fact_acceptance_enabled",
    "connector_binding_enabled",
    "runtime_enabled",
    "live_enabled",
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "order_execution_enabled",
    "profit_claim_enabled",
    "atomicrows_bundle_creation_enabled",
    "sha_freeze_enabled",
}

REGISTRY_AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "source_required": True,
    "execution_disabled": True,
    "candidate_records_are_not_accepted_source_evidence": True,
    "accepted_records_are_schema_only_without_external_fact_authority_flag": True,
    "accepted_fact_claims_require_accepted_source_packet_authority_flag": True,
    "accepted_source_packet_authority_required_before_ledger_current": True,
    "target_field_scope_required": True,
    "wildcard_scope_allowed": False,
    "connector_semantic_binding_allowed": False,
    "runtime_use_allowed": False,
}

REGISTRY_FIXTURE_REQUIRED_ROOT_FIELDS = {
    "fixture_id",
    "fixture_authority_class",
    "example_authority_class",
    "mode",
    "execution",
    "schema_authority_class",
    "surface_version",
    "fixture_no_claim_flags",
    "no_claim_flags",
    "source_evidence_acceptance_registry",
}

REGISTRY_REQUIRED_RECORD_COLLECTIONS = {
    "candidate_records",
    "accepted_records",
}


def _load_schema(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"schema file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"schema file is not valid JSON: {exc}"]
    if not isinstance(value, dict):
        return None, ["schema file must contain a JSON object"]
    return value, []


def _read_owner_packet(path: pathlib.Path) -> tuple[str | None, list[str]]:
    if not path.exists():
        return None, [f"owner packet is missing: {path}"]
    return path.read_text(encoding="utf-8"), []


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


def _validate_owner_packet(text: str) -> list[str]:
    failures: list[str] = []
    required_markers = {
        "v1.3A packet_version marker": PACKET_VERSION_MARKER,
        "external fact authority blocked marker": EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER,
        "connector semantic population blocked marker": CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER,
        "no source-fact retrieval marker": PACKET_RETRIEVES_NO_FACTS_MARKER,
        "no source-fact acceptance marker": PACKET_ACCEPTS_NO_FACTS_MARKER,
    }
    for label, marker in required_markers.items():
        if marker not in text:
            failures.append(f"owner packet missing {label}")
    return failures


def _validate_schema_surfaces(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema missing $defs object"]

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

    return failures


def _validate_no_authority(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs", {})
    defs = defs if isinstance(defs, dict) else {}

    if schema.get("properties", {}).get("execution", {}).get("const") != "DISABLED":
        failures.append("root execution must be DISABLED")
    if (
        schema.get("properties", {})
        .get("schema_authority_class", {})
        .get("const")
        != "STATIC_SCHEMA_CONTRACT_ONLY_NOT_EXTERNAL_FACT_AUTHORITY"
    ):
        failures.append("root schema authority must be static and not external fact authority")

    no_claims = defs.get("no_claim_flags")
    if not isinstance(no_claims, dict):
        failures.append("schema missing no_claim_flags definition")
    else:
        no_claim_properties = _properties(no_claims)
        no_claim_required = _required(no_claims)
        for field in sorted(FORBIDDEN_AUTHORITY_FIELDS):
            if field not in no_claim_properties:
                failures.append(f"no_claim_flags missing authority block field: {field}")
                continue
            if field not in no_claim_required:
                failures.append(f"no_claim_flags does not require authority block field: {field}")
            if _const_value(no_claims, field) is not False:
                failures.append(f"no_claim_flags must set {field} to const false")

    accepted_surface = defs.get("accepted_source_packet")
    if isinstance(accepted_surface, dict):
        for field in sorted(REQUIRED_TRUE_NO_RUNTIME_FLAGS):
            if _const_value(accepted_surface, field) is not True:
                failures.append(f"accepted_source_packet must set {field} to const true")

    candidate_surface = defs.get("candidate_source_packet")
    if isinstance(candidate_surface, dict) and (
        _const_value(candidate_surface, "candidate_packet_may_unlock_connector_semantics")
        is not False
    ):
        failures.append("candidate packet must not unlock connector semantics")

    ledger_surface = defs.get("target_field_ledger_record")
    if isinstance(ledger_surface, dict) and (
        _const_value(ledger_surface, "connector_semantic_binding_allowed_flag") is not False
    ):
        failures.append("target-field ledger must not allow connector binding in PR4 schema")

    registry_surface = defs.get("source_evidence_acceptance_registry")
    if isinstance(registry_surface, dict):
        if _const_value(registry_surface, "mode") != "SOURCE_REQUIRED":
            failures.append("source-evidence registry mode must be SOURCE_REQUIRED")
        if _const_value(registry_surface, "execution") != "DISABLED":
            failures.append("source-evidence registry execution must be DISABLED")
        if _const_value(registry_surface, "deterministic_output") is not True:
            failures.append("source-evidence registry must declare deterministic output")
        if _const_value(registry_surface, "registry_authority_class") != (
            "STATIC_SOURCE_EVIDENCE_ACCEPTANCE_REGISTRY_SCAFFOLD_NOT_RUNTIME_AUTHORITY"
        ):
            failures.append("source-evidence registry authority class must be static-only")

    candidate_registry_record = defs.get("registry_candidate_source_evidence_record")
    if isinstance(candidate_registry_record, dict):
        if _const_value(candidate_registry_record, "accepted_fact_claim_present") is not False:
            failures.append("candidate registry records must not claim accepted facts")
        if (
            _const_value(
                candidate_registry_record,
                "accepted_source_packet_authority_present",
            )
            is not False
        ):
            failures.append("candidate registry records must not claim accepted-packet authority")

    accepted_registry_record = defs.get("registry_accepted_source_evidence_record")
    if isinstance(accepted_registry_record, dict):
        if _const_value(accepted_registry_record, "accepted_fact_claim_present") is not False:
            failures.append("accepted registry records must not claim accepted facts")
        if (
            _const_value(
                accepted_registry_record,
                "accepted_source_packet_authority_present",
            )
            is not False
        ):
            failures.append("accepted registry records must not claim accepted-packet authority")
        if (
            _const_value(
                accepted_registry_record,
                "connector_semantic_binding_allowed_flag",
            )
            is not False
        ):
            failures.append("accepted registry records must not allow connector binding")

    registry_forbidden_flags = defs.get("registry_forbidden_action_flags")
    if isinstance(registry_forbidden_flags, dict):
        flag_properties = _properties(registry_forbidden_flags)
        flag_required = _required(registry_forbidden_flags)
        for field in sorted(REGISTRY_FORBIDDEN_ACTION_FLAGS):
            if field not in flag_properties:
                failures.append(f"registry forbidden flags missing field: {field}")
                continue
            if field not in flag_required:
                failures.append(f"registry forbidden flags must require field: {field}")
            if _const_value(registry_forbidden_flags, field) is not False:
                failures.append(f"registry forbidden flag {field} must be const false")

    registry_scope_flags = defs.get("registry_authority_scope_flags")
    if isinstance(registry_scope_flags, dict):
        scope_properties = _properties(registry_scope_flags)
        scope_required = _required(registry_scope_flags)
        for field, expected in sorted(REGISTRY_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
            if field not in scope_properties:
                failures.append(f"registry authority/scope flags missing field: {field}")
                continue
            if field not in scope_required:
                failures.append(f"registry authority/scope flags must require field: {field}")
            if _const_value(registry_scope_flags, field) is not expected:
                failures.append(
                    f"registry authority/scope flag {field} must be const {expected}"
                )

    return failures


def _validate_examples(schema: dict[str, Any]) -> list[str]:
    examples = schema.get("examples")
    if not isinstance(examples, list) or not examples:
        return ["schema must include at least one synthetic non-authoritative example"]
    for index, example in enumerate(examples):
        if not isinstance(example, dict):
            return [f"schema example {index} must be an object"]
        if example.get("example_authority_class") != (
            "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
        ):
            return [f"schema example {index} must be marked synthetic and non-authoritative"]
    return []


def _mapping_at(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _list_at(value: dict[str, Any], field: str, label: str) -> tuple[list[Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, list) or not item:
        return None, [f"{label}.{field} must be a non-empty list"]
    return item, []


def _require_mapping_fields(
    value: dict[str, Any], required_fields: set[str], label: str
) -> list[str]:
    missing = sorted(required_fields - set(value))
    if not missing:
        return []
    return [f"{label} missing required fields: {', '.join(missing)}"]


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
        set(REGISTRY_AUTHORITY_SCOPE_FLAG_EXPECTATIONS),
        label,
    )
    for field, expected in sorted(REGISTRY_AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
        if field in value and value[field] is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def _walk_registry_values(value: Any, path: str = "registry"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk_registry_values(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_registry_values(item, f"{path}[{index}]")


def _validate_no_forbidden_true_values(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden_false_fields = (
        REGISTRY_FORBIDDEN_ACTION_FLAGS
        | FORBIDDEN_AUTHORITY_FIELDS
        | {
            "retrieves_source_facts",
            "accepts_source_facts",
            "creates_accepted_source_evidence",
            "unlocks_connector_semantics",
            "creates_runtime_cash_receipts",
            "creates_live_reachability",
            "executes_orders",
            "creates_profit_evidence",
            "accepted_fact_claim_present",
            "accepted_source_packet_authority_present",
            "connector_semantic_binding_allowed_flag",
        }
    )
    for path, key, item in _walk_registry_values(value):
        if key in forbidden_false_fields and item is not False:
            failures.append(f"{path} must be false")
    return failures


def _validate_records_have_target_field_scope(
    records: list[Any], *, collection_label: str, field_name: str
) -> list[str]:
    failures: list[str] = []
    for index, record in enumerate(records):
        label = f"{collection_label}[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{label} must be an object")
            continue
        if field_name == "target_field_paths":
            paths = record.get(field_name)
            if not isinstance(paths, list) or not paths:
                failures.append(f"{label}.{field_name} must be a non-empty list")
                continue
            for item in paths:
                if not isinstance(item, str) or "*" in item:
                    failures.append(f"{label}.{field_name} must contain scoped field paths")
        else:
            path = record.get(field_name)
            if not isinstance(path, str) or not path or "*" in path:
                failures.append(f"{label}.{field_name} must be a scoped field path")
    return failures


def validate_acceptance_registry_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(
        _require_mapping_fields(
            fixture,
            REGISTRY_FIXTURE_REQUIRED_ROOT_FIELDS,
            "registry fixture",
        )
    )

    if fixture.get("fixture_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT"
    ):
        failures.append("registry fixture must be synthetic and non-authoritative")
    if fixture.get("example_authority_class") != (
        "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
    ):
        failures.append("registry fixture example authority must be synthetic")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("registry fixture mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("registry fixture execution must be DISABLED")

    fixture_no_claim_flags, flag_failures = _mapping_at(
        fixture, "fixture_no_claim_flags", "registry fixture"
    )
    failures.extend(flag_failures)
    if fixture_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                fixture_no_claim_flags,
                {
                    "retrieves_source_facts",
                    "accepts_source_facts",
                    "creates_accepted_source_evidence",
                    "unlocks_connector_semantics",
                    "creates_runtime_cash_receipts",
                    "creates_live_reachability",
                    "executes_orders",
                    "creates_profit_evidence",
                },
                "registry fixture.fixture_no_claim_flags",
            )
        )

    no_claim_flags, no_claim_failures = _mapping_at(
        fixture, "no_claim_flags", "registry fixture"
    )
    failures.extend(no_claim_failures)
    if no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                no_claim_flags,
                FORBIDDEN_AUTHORITY_FIELDS,
                "registry fixture.no_claim_flags",
            )
        )

    registry, registry_failures = _mapping_at(
        fixture,
        "source_evidence_acceptance_registry",
        "registry fixture",
    )
    failures.extend(registry_failures)
    if registry is None:
        return failures

    failures.extend(
        _require_mapping_fields(
            registry,
            {
                "registry_type",
                "registry_id",
                "registry_authority_class",
                "mode",
                "execution",
                "deterministic_output",
                "registry_authority_scope_flags",
                "registry_forbidden_action_flags",
                "candidate_records",
                "accepted_records",
                "validation_hook_ids",
                "no_claim_flags",
            },
            "source_evidence_acceptance_registry",
        )
    )
    if registry.get("registry_type") != (
        "SOURCE_EVIDENCE_ACCEPTANCE_REGISTRY_STATIC_SCAFFOLD"
    ):
        failures.append("registry_type must be static scaffold")
    if registry.get("registry_authority_class") != (
        "STATIC_SOURCE_EVIDENCE_ACCEPTANCE_REGISTRY_SCAFFOLD_NOT_RUNTIME_AUTHORITY"
    ):
        failures.append("registry_authority_class must be static non-runtime")
    if registry.get("mode") != "SOURCE_REQUIRED":
        failures.append("registry mode must be SOURCE_REQUIRED")
    if registry.get("execution") != "DISABLED":
        failures.append("registry execution must be DISABLED")
    if registry.get("deterministic_output") is not True:
        failures.append("registry deterministic_output must be true")

    scope_flags, scope_failures = _mapping_at(
        registry,
        "registry_authority_scope_flags",
        "source_evidence_acceptance_registry",
    )
    failures.extend(scope_failures)
    if scope_flags is not None:
        failures.extend(
            _validate_authority_scope_flag_map(
                scope_flags,
                "source_evidence_acceptance_registry.registry_authority_scope_flags",
            )
        )

    registry_forbidden_flags, registry_flag_failures = _mapping_at(
        registry,
        "registry_forbidden_action_flags",
        "source_evidence_acceptance_registry",
    )
    failures.extend(registry_flag_failures)
    if registry_forbidden_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                registry_forbidden_flags,
                REGISTRY_FORBIDDEN_ACTION_FLAGS,
                "source_evidence_acceptance_registry.registry_forbidden_action_flags",
            )
        )

    registry_no_claim_flags, registry_no_claim_failures = _mapping_at(
        registry,
        "no_claim_flags",
        "source_evidence_acceptance_registry",
    )
    failures.extend(registry_no_claim_failures)
    if registry_no_claim_flags is not None:
        failures.extend(
            _validate_false_flag_map(
                registry_no_claim_flags,
                FORBIDDEN_AUTHORITY_FIELDS,
                "source_evidence_acceptance_registry.no_claim_flags",
            )
        )

    candidate_records, candidate_failures = _list_at(
        registry,
        "candidate_records",
        "source_evidence_acceptance_registry",
    )
    failures.extend(candidate_failures)
    if candidate_records is not None:
        failures.extend(
            _validate_records_have_target_field_scope(
                candidate_records,
                collection_label="source_evidence_acceptance_registry.candidate_records",
                field_name="target_field_paths",
            )
        )

    accepted_records, accepted_failures = _list_at(
        registry,
        "accepted_records",
        "source_evidence_acceptance_registry",
    )
    failures.extend(accepted_failures)
    if accepted_records is not None:
        failures.extend(
            _validate_records_have_target_field_scope(
                accepted_records,
                collection_label="source_evidence_acceptance_registry.accepted_records",
                field_name="target_field_path",
            )
        )
        for index, record in enumerate(accepted_records):
            if not isinstance(record, dict):
                continue
            label = f"source_evidence_acceptance_registry.accepted_records[{index}]"
            if (
                record.get("accepted_fact_claim_present") is True
                and record.get("accepted_source_packet_authority_present") is not True
            ):
                failures.append(
                    f"{label} accepted fact claim requires accepted-source packet authority"
                )

    failures.extend(_validate_no_forbidden_true_values(fixture))
    return failures


def validate_static_surface(
    *,
    schema_path: pathlib.Path,
    owner_packet_path: pathlib.Path,
    registry_fixture_path: pathlib.Path | None = None,
) -> list[str]:
    failures: list[str] = []
    schema, schema_failures = _load_schema(schema_path)
    failures.extend(schema_failures)
    packet_text, packet_failures = _read_owner_packet(owner_packet_path)
    failures.extend(packet_failures)
    registry_fixture: dict[str, Any] | None = None
    if registry_fixture_path is not None:
        registry_fixture, registry_fixture_failures = _load_schema(registry_fixture_path)
        failures.extend(registry_fixture_failures)

    if packet_text is not None:
        failures.extend(_validate_owner_packet(packet_text))
    if schema is not None:
        failures.extend(_validate_schema_surfaces(schema))
        failures.extend(_validate_no_authority(schema))
        failures.extend(_validate_examples(schema))
    if registry_fixture is not None:
        failures.extend(validate_acceptance_registry_fixture(registry_fixture))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True)
    parser.add_argument("--owner-packet", required=True)
    parser.add_argument("--registry-fixture")
    args = parser.parse_args()

    failures = validate_static_surface(
        schema_path=pathlib.Path(args.schema),
        owner_packet_path=pathlib.Path(args.owner_packet),
        registry_fixture_path=(
            pathlib.Path(args.registry_fixture) if args.registry_fixture else None
        ),
    )
    if failures:
        raise SystemExit(
            "SOURCE_EVIDENCE_STATIC_VALIDATION_FAILED\n- " + "\n- ".join(failures)
        )
    print("SOURCE_EVIDENCE_STATIC_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
