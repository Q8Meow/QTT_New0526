from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


DEFAULT_STATE_MACHINE_PATH = (
    Path(__file__).resolve().parent / "source_retrieval_state_machine.json"
)
STATE_MACHINE_ARTIFACT = (
    "src/qtt/source_evidence/retrieval/source_retrieval_state_machine.json"
)

REQUIRED_STATE_FIELDS = {
    "accepted_fact_authority_flag",
    "allowed_next_states",
    "authority_class",
    "block_code",
    "block_reason_canonical",
    "blocked_next_states",
    "candidate_receipt_allowed_flag",
    "connector_semantic_unlock_allowed_flag",
    "order_authority_allowed_flag",
    "profit_evidence_allowed_flag",
    "quantum_backend_execution_allowed_flag",
    "requires_accepted_source_packet_flag",
    "requires_conflict_clearance_flag",
    "requires_fresh_revalidation_flag",
    "requires_owner_review_flag",
    "runtime_live_use_allowed_flag",
    "source_change_materiality_default",
    "state_family",
    "state_id",
}

REQUIRED_TARGET_FIELDS = {
    "retrieval_target_id",
    "platform_scope",
    "venue_id",
    "market_scope_class",
    "source_class",
    "source_target_type",
    "source_locator",
    "target_field_path",
    "semantic_family",
    "capture_requirement",
    "locator_requirement",
    "digest_requirement",
    "redaction_requirement",
    "revalidation_requirement",
    "source_change_materiality_default",
    "source_authority_state",
    "connector_unlock_state",
    "runtime_live_use_state",
    "quantum_execution_state",
    "allowed_next_states",
    "block_code",
    "block_reason",
    "owner_review_required_flag",
    "candidate_receipt_allowed_flag",
    "accepted_fact_authority_flag",
    "connector_semantic_unlock_allowed_flag",
    "runtime_live_use_allowed_flag",
    "order_authority_allowed_flag",
    "profit_evidence_allowed_flag",
    "quantum_backend_execution_allowed_flag",
}

REQUIRED_CANDIDATE_RECEIPT_FIELDS = {
    "accepted_fact_authority_flag",
    "canonicalization_policy_id",
    "connector_semantic_unlock_allowed_flag",
    "fetch_or_capture_metadata",
    "fetch_or_capture_mode",
    "next_required_gate",
    "order_authority_allowed_flag",
    "profit_evidence_allowed_flag",
    "quantum_backend_execution_allowed_flag",
    "redaction_applied_flag",
    "retrieval_receipt_id",
    "retrieval_target_id",
    "runtime_live_use_allowed_flag",
    "secret_like_value_detected_flag",
    "source_authority_state",
    "source_class",
    "source_locator",
}

FORCED_FALSE_AUTHORITY_FLAGS = (
    "accepted_fact_authority_flag",
    "connector_semantic_unlock_allowed_flag",
    "runtime_live_use_allowed_flag",
    "order_authority_allowed_flag",
    "profit_evidence_allowed_flag",
    "quantum_backend_execution_allowed_flag",
)

ACTIVE_STAGE1_PLATFORM_SCOPES = {
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
}

FUTURE_MARKET_FAMILIES = {
    "COMMODITIES",
    "CRYPTOCURRENCY",
    "EQUITIES",
    "ETFS",
    "FUTURES",
    "FX",
    "OPTIONS",
    "STOCKS",
}

FORBIDDEN_MARKET_TAXONOMY_VALUES = {
    "ANY_OTHER_MARKET",
    "OTHER",
    "OTHER_OWNER_APPROVED_FUTURE_MARKET",
    "UNKNOWN_MARKET",
    "etc.",
}

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)


def load_state_machine(path: Path | None = None) -> dict[str, Any]:
    machine_path = DEFAULT_STATE_MACHINE_PATH if path is None else path
    value = json.loads(machine_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"state machine root must be an object: {machine_path}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def state_records(machine: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = machine.get("state_records")
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def state_by_id(machine: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        record["state_id"]: record
        for record in state_records(machine)
        if isinstance(record.get("state_id"), str)
    }


def state_machine_failures(machine: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    records = state_records(machine)
    if not records:
        return ["state machine must define state_records"]

    ids = [record.get("state_id") for record in records]
    if len(ids) != len(set(ids)):
        failures.append("state machine state_id values must be unique")

    ids_set = {item for item in ids if isinstance(item, str)}
    for index, record in enumerate(records):
        label = f"state_records[{index}]"
        missing = sorted(REQUIRED_STATE_FIELDS - set(record))
        if missing:
            failures.append(f"{label} missing fields: {', '.join(missing)}")
        for flag in FORCED_FALSE_AUTHORITY_FLAGS:
            if record.get(flag) is not False:
                failures.append(f"{label}.{flag} must be false")
        for field in ("allowed_next_states", "blocked_next_states"):
            values = record.get(field)
            if not isinstance(values, list) or not all(
                isinstance(item, str) for item in values
            ):
                failures.append(f"{label}.{field} must be a list of state IDs")
                continue
            unknown = sorted(set(values) - ids_set)
            if unknown:
                failures.append(f"{label}.{field} contains unknown states: {unknown}")

    for required in (
        "OWNER_SOURCE_DEFINITIONS_PACKET_MISSING",
        "OWNER_SOURCE_DEFINITIONS_PACKET_PRESENT_NOT_APPROVED",
        "OWNER_SOURCE_DEFINITIONS_PACKET_APPROVED_FOR_RETRIEVAL_SCOPE",
        "SOURCE_TARGET_DECLARED_NOT_RETRIEVED",
        "SOURCE_RETRIEVAL_MANIFEST_READY",
        "SOURCE_RETRIEVAL_ATTEMPTED_FIXTURE_ONLY",
        "SOURCE_RETRIEVAL_ATTEMPTED_EXTERNAL_GATED_DISABLED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_CREATED_NOT_ACCEPTED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_CONFLICTED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_STALE",
        "SOURCE_BLOCKED_SECRET_OR_PRIVATE_VALUE_DETECTED",
        "SOURCE_BLOCKED_PRIVATE_DOC_UNCLEAR_ACCESS_RIGHTS",
        "SOURCE_BLOCKED_NON_AUTHORITATIVE_SOURCE_CLASS",
        "SOURCE_ACCEPTANCE_REQUIRED_NOT_PERFORMED",
        "CONNECTOR_BINDING_BLOCKED_PENDING_ACCEPTED_TARGET_FIELD_PACKET",
        "RUNTIME_LIVE_USE_BLOCKED_PENDING_ACCEPTED_SOURCE_AND_CONNECTOR_BINDING",
        "QUANTUM_BACKEND_EXECUTION_BLOCKED_METADATA_ONLY",
    ):
        if required not in ids_set:
            failures.append(f"state machine missing required state: {required}")

    if set(machine.get("active_stage1_platform_scopes", [])) != ACTIVE_STAGE1_PLATFORM_SCOPES:
        failures.append("active Stage-1 platform scopes must match canonical scope")
    if FORBIDDEN_MARKET_TAXONOMY_VALUES - set(
        machine.get("forbidden_market_taxonomy_values", [])
    ):
        failures.append("forbidden market taxonomy registry is incomplete")
    if set(machine.get("future_market_families", [])) != FUTURE_MARKET_FAMILIES:
        failures.append("future market family registry must match canonical taxonomy")

    return failures


def classify_market_scope(value: str) -> str:
    if value in ACTIVE_STAGE1_PLATFORM_SCOPES:
        return value
    if value in FUTURE_MARKET_FAMILIES:
        return value
    if value in FORBIDDEN_MARKET_TAXONOMY_VALUES:
        raise ValueError(f"forbidden market taxonomy value: {value}")
    return "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"


def _missing_fields(record: Mapping[str, Any], required: set[str]) -> list[str]:
    return sorted(required - set(record))


def _validate_forced_false_flags(record: Mapping[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for field in FORCED_FALSE_AUTHORITY_FLAGS:
        if record.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_retrieval_target_record(
    record: Mapping[str, Any], machine: Mapping[str, Any] | None = None
) -> list[str]:
    failures = [
        f"retrieval target missing fields: {', '.join(missing)}"
        for missing in [_missing_fields(record, REQUIRED_TARGET_FIELDS)]
        if missing
    ]
    failures.extend(_validate_forced_false_flags(record, "retrieval target"))
    if "*" in str(record.get("target_field_path", "")):
        failures.append("retrieval target target_field_path must not be wildcard")

    machine = load_state_machine() if machine is None else machine
    states = state_by_id(machine)
    for field in (
        "source_authority_state",
        "connector_unlock_state",
        "runtime_live_use_state",
        "quantum_execution_state",
    ):
        value = record.get(field)
        if isinstance(value, str) and value not in states:
            failures.append(f"retrieval target {field} is not a controller state: {value}")

    return failures


def validate_candidate_receipt_record(
    record: Mapping[str, Any], machine: Mapping[str, Any] | None = None
) -> list[str]:
    failures = [
        f"candidate receipt missing fields: {', '.join(missing)}"
        for missing in [_missing_fields(record, REQUIRED_CANDIDATE_RECEIPT_FIELDS)]
        if missing
    ]
    failures.extend(_validate_forced_false_flags(record, "candidate receipt"))
    if record.get("source_authority_state") != "CANDIDATE_RETRIEVAL_ONLY_NOT_ACCEPTED_FACT":
        failures.append("candidate receipt source_authority_state must be candidate-only")
    if record.get("next_required_gate") != (
        "ACCEPTED_SOURCE_EVIDENCE_PACKET_REQUIRED_FOR_TARGET_FIELD"
    ):
        failures.append("candidate receipt next_required_gate must require accepted packet")
    if record.get("fetch_or_capture_mode") == "FIXTURE_ONLY" and not record.get("fixture_id"):
        failures.append("candidate receipt fixture mode requires fixture_id")
    if not record.get("declared_no_content_block_state") and not (
        record.get("quote_span_locator") or record.get("machine_field_locator")
    ):
        failures.append(
            "candidate receipt requires quote_span_locator or machine_field_locator"
        )

    machine = load_state_machine() if machine is None else machine
    if record.get("source_authority_state") not in state_by_id(machine):
        failures.append("candidate receipt source_authority_state is not controller-defined")
    return failures


def validate_retrieval_manifest(
    manifest: Mapping[str, Any], machine: Mapping[str, Any] | None = None
) -> list[str]:
    failures: list[str] = []
    machine = load_state_machine() if machine is None else machine
    if manifest.get("external_network_fetch_default_enabled") is not False:
        failures.append("manifest must default external network fetch to false")
    if manifest.get("accepted_source_fact_count") != 0:
        failures.append("manifest accepted_source_fact_count must be 0")
    if manifest.get("accepted_source_packet_created_count") != 0:
        failures.append("manifest accepted_source_packet_created_count must be 0")
    targets = manifest.get("retrieval_targets", [])
    if not isinstance(targets, list):
        failures.append("manifest retrieval_targets must be a list")
        return failures
    for index, target in enumerate(targets):
        if not isinstance(target, Mapping):
            failures.append(f"manifest retrieval_targets[{index}] must be an object")
        else:
            failures.extend(validate_retrieval_target_record(target, machine))
    return failures


def redact_secret_like_values(text: str) -> tuple[str, bool]:
    redacted = text
    detected = False
    for pattern in SECRET_VALUE_PATTERNS:
        redacted, count = pattern.subn("[REDACTED_SECRET_LIKE_VALUE]", redacted)
        detected = detected or count > 0
    return redacted, detected


def private_doc_access_state(access_rights_clear: bool) -> str:
    if access_rights_clear:
        return "PRIVATE_DOC_ACCESS_RIGHTS_ATTESTED_OWNER_REVIEW_STILL_REQUIRED"
    return "SOURCE_BLOCKED_PRIVATE_DOC_UNCLEAR_ACCESS_RIGHTS"


def stable_report(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_stable_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_report(value), encoding="utf-8", newline="\n")


def state_summary(machine: Mapping[str, Any]) -> dict[str, Any]:
    records = state_records(machine)
    return {
        "block_codes": [record["block_code"] for record in records],
        "controller_state_count": len(records),
        "state_ids": [record["state_id"] for record in records],
        "state_machine_digest_sha256": canonical_digest(machine),
    }


def controller_reference(machine: Mapping[str, Any], state_id: str) -> dict[str, Any]:
    states = state_by_id(machine)
    state = states[state_id]
    return {
        "block_code": state["block_code"],
        "block_reason_source": STATE_MACHINE_ARTIFACT,
        "state_id": state_id,
    }


def target_derivation_block(machine: Mapping[str, Any]) -> dict[str, Any]:
    state_id = "SOURCE_TARGET_DERIVATION_BLOCKED_AMBIGUOUS_CANONICAL_TARGET_RECORDS"
    state = state_by_id(machine)[state_id]
    return {
        "block_code": state["block_code"],
        "block_reason_canonical": state["block_reason_canonical"],
        "block_reason_loaded_from_central_state_machine": True,
        "block_reason_source": STATE_MACHINE_ARTIFACT,
        "state_id": state_id,
    }


def sorted_unique(values: Sequence[str]) -> list[str]:
    return sorted(set(values))
