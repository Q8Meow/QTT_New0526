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


def validate_static_surface(
    *, schema_path: pathlib.Path, owner_packet_path: pathlib.Path
) -> list[str]:
    failures: list[str] = []
    schema, schema_failures = _load_schema(schema_path)
    failures.extend(schema_failures)
    packet_text, packet_failures = _read_owner_packet(owner_packet_path)
    failures.extend(packet_failures)

    if packet_text is not None:
        failures.extend(_validate_owner_packet(packet_text))
    if schema is not None:
        failures.extend(_validate_schema_surfaces(schema))
        failures.extend(_validate_no_authority(schema))
        failures.extend(_validate_examples(schema))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True)
    parser.add_argument("--owner-packet", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        schema_path=pathlib.Path(args.schema),
        owner_packet_path=pathlib.Path(args.owner_packet),
    )
    if failures:
        raise SystemExit(
            "SOURCE_EVIDENCE_STATIC_VALIDATION_FAILED\n- " + "\n- ".join(failures)
        )
    print("SOURCE_EVIDENCE_STATIC_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
