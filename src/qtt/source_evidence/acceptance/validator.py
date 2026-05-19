from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


ACCEPTED_TOOL = "tools/source_evidence_acceptance_executor.py"
DETERMINISTIC_FIXTURE_TIMESTAMP = "2026-05-19T00:00:00Z"

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

OFFICIAL_SOURCE_CLASSES = {
    "OFFICIAL_VENUE_DOCS",
    "OFFICIAL_API_DOCS",
    "OFFICIAL_SDK_DOCS",
    "OFFICIAL_RULEBOOKS",
    "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
    "OFFICIAL_PROVIDER_DOCS",
}

TEST_FIXTURE_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"
SOURCE_CLASSES = OFFICIAL_SOURCE_CLASSES | {TEST_FIXTURE_CLASS}

PLACEHOLDER_LOCATOR_TYPES = {
    "PLACEHOLDER_NOT_FACTUAL_URL",
    "FIXTURE_ONLY",
    "OWNER_UNSET_PENDING_OFFICIAL_SOURCE_DISCOVERY",
}

VALID_LOCATOR_TYPES = {
    "OFFICIAL_URL",
    "OFFICIAL_DOC_PATH",
    "OFFICIAL_MACHINE_PAYLOAD_PATH",
    "OWNER_UPLOADED_PRIVATE_DOC_LOCATOR",
    "PLACEHOLDER_NOT_FACTUAL_URL",
    "FIXTURE_ONLY",
}

VALID_EXTRACTED_FACT_TYPES = {
    "STRING",
    "NUMBER",
    "BOOLEAN",
    "OBJECT",
    "ARRAY",
    "ENUM",
    "NO_VALUE_REASON",
}

VALID_CONFLICT_STATES = {
    "NO_CONFLICT",
    "ACCEPTABLE_DUPLICATE",
    "OWNER_REVIEWED_EXACT_EVIDENCE",
}

VALID_CONFLICT_RESOLUTION_STATES = {
    "NO_CONFLICT",
    "NO_PRIOR_PACKET_FOR_TARGET_FIELD",
    "ACCEPTABLE_DUPLICATE",
    "OWNER_REVIEWED_EXACT_EVIDENCE",
}

VALID_REVALIDATION_TRIGGERS = {
    "TIME_BASED",
    "EVENT_BASED",
    "TIME_OR_EVENT_BASED",
}

FRESH_REVALIDATION_STATES = {
    "CURRENT",
    "FRESH",
    "TEST_FIXTURE_CURRENT",
}

FRESH_REVALIDATION_DUE_CONDITIONS = {
    "NOT_DUE_CURRENT",
    "EVENT_TRIGGERED_IMMEDIATE_WHEN_SOURCE_CHANGES",
}

SAFE_REDACTION_STATES = {
    "NO_SECRET_DETECTED",
    "REDACTED_SECRET_ALIAS_ONLY",
    "TEST_FIXTURE_NO_SECRET",
}

SAFE_PRIVATE_DOC_STATES = {
    "PUBLIC_SOURCE_NOT_PRIVATE",
    "PUBLIC_OR_FIXTURE_ACCESS_NOT_PRIVATE",
    "OWNER_UPLOADED_PRIVATE_DOC_ACCESS_RIGHTS_ATTESTED",
    "TEST_FIXTURE_NOT_PRIVATE_DOC",
}

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)

TARGET_FIELD_RE = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


REQUIRED_CANDIDATE_FIELDS = {
    "candidate_source_evidence_packet_record_type",
    "candidate_source_evidence_packet_id",
    "candidate_source_evidence_packet_version",
    "master_plan_edition",
    "retrieval_manifest_id",
    "retrieval_target_id",
    "source_target_id",
    "venue_id",
    "platform_scope",
    "source_locator",
    "source_locator_type",
    "source_locator_status",
    "source_authority_class",
    "source_access_method",
    "source_retrieval_method",
    "source_retrieved_at_utc",
    "raw_capture_digest_sha256",
    "canonical_text_digest_sha256",
    "source_digest_sha256",
    "quote_span_locator_or_machine_field_locator",
    "exact_quote_or_machine_field_locator",
    "extracted_fact_payload",
    "extracted_fact_type",
    "extracted_fact",
    "accepted_value_label",
    "target_section_id",
    "target_field_paths_authorized",
    "target_field_path",
    "applicability_scope",
    "conflict_check_id",
    "conflict_resolution_state",
    "conflict_state",
    "revalidation_trigger",
    "revalidation_trigger_id",
    "revalidation_due_at_or_event",
    "revalidation_due_condition",
    "revalidation_state",
    "redaction_state",
    "private_doc_access_rights_state",
    "source_change_materiality_class",
    "supersedes_packet_ids",
    "production_external_fact_authority",
    "no_connector_semantic_population_flag",
    "no_live_reachability_flag",
    "no_order_execution_flag",
    "no_runtime_cash_claim_flag",
    "no_blocker_reduction_or_profit_claim_flag",
    "no_claim_flags",
}

REQUIRED_ACCEPTED_PACKET_FIELDS = {
    "accepted_packet_record_type",
    "accepted_source_evidence_packet_id",
    "accepted_source_evidence_packet_version",
    "master_plan_edition",
    "candidate_source_evidence_packet_id",
    "acceptance_decision_packet_id",
    "retrieval_manifest_id",
    "source_target_id",
    "retrieval_target_id",
    "venue_id",
    "platform_scope",
    "source_locator",
    "source_locator_type",
    "source_locator_status",
    "source_authority_class",
    "source_access_method",
    "source_retrieval_method",
    "source_retrieved_at_utc",
    "raw_capture_digest_sha256",
    "canonical_text_digest_sha256",
    "source_digest_sha256",
    "quote_span_locator_or_machine_field_locator",
    "exact_quote_or_machine_field_locator",
    "extracted_fact_payload",
    "extracted_fact_type",
    "extracted_fact",
    "accepted_value_label",
    "target_section_id",
    "target_field_paths_authorized",
    "target_field_path",
    "applicability_scope",
    "conflict_check_id",
    "conflict_resolution_state",
    "conflict_state",
    "revalidation_trigger",
    "revalidation_trigger_id",
    "revalidation_due_at_or_event",
    "revalidation_due_condition",
    "supersedes_packet_ids",
    "accepted_at_utc",
    "accepted_by_tool",
    "receipt_ids",
    "production_external_fact_authority",
    "no_connector_semantic_population_flag",
    "no_live_reachability_flag",
    "no_order_execution_flag",
    "no_runtime_cash_claim_flag",
    "no_blocker_reduction_or_profit_claim_flag",
    "no_claim_flags",
}

NO_CLAIM_FLAGS = {
    "connector_semantic_binding_created": False,
    "connector_semantic_value_populated": False,
    "runtime_resolver_snapshot_created": False,
    "runtime_live_authority_created": False,
    "order_authority_created": False,
    "runtime_cash_receipt_created": False,
    "replay_paper_result_created": False,
    "profit_evidence_created": False,
    "latency_superiority_claim_created": False,
    "execution_superiority_claim_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "optimizer_execution_created": False,
    "quantum_advantage_claim_created": False,
    "atomicrows_bundle_created": False,
    "atomicrows_sha_created": False,
}


@dataclass(frozen=True)
class ExecuteAcceptanceResult:
    decision_receipt: dict[str, Any]
    accepted_packet: dict[str, Any] | None
    accepted_ledger_record: dict[str, Any] | None
    conflict_report: dict[str, Any]
    revalidation_status: dict[str, Any]
    reject_receipt: dict[str, Any] | None


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def default_no_claim_flags() -> dict[str, bool]:
    return dict(NO_CLAIM_FLAGS)


def stable_report(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _has_secret_like_value(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)
    if isinstance(value, Mapping):
        return any(_has_secret_like_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_secret_like_value(item) for item in value)
    return False


def _validate_target_field_path(value: Any, label: str, failures: list[str]) -> None:
    if not isinstance(value, str) or not TARGET_FIELD_RE.fullmatch(value) or "*" in value:
        failures.append(f"{label} must be an exact non-wildcard target field path")


def _validate_no_claim_flags(value: Any, label: str, failures: list[str]) -> None:
    if not isinstance(value, Mapping):
        failures.append(f"{label} must be an object")
        return
    missing = sorted(set(NO_CLAIM_FLAGS) - set(value))
    if missing:
        failures.append(f"{label} missing no-claim flags: {', '.join(missing)}")
    for field, expected in sorted(NO_CLAIM_FLAGS.items()):
        if value.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")


def _candidate_is_fixture(candidate: Mapping[str, Any]) -> bool:
    return candidate.get("fixture_authority_class") == TEST_FIXTURE_CLASS


def _failure_code(message: str) -> str:
    if "digest" in message:
        return "MISSING_OR_MALFORMED_DIGEST"
    if "target_field" in message or "scope" in message:
        return "TARGET_FIELD_OR_SCOPE_INVALID"
    if "conflict" in message:
        return "CONFLICT_STATE_BLOCKED"
    if "revalidation" in message or "stale" in message:
        return "REVALIDATION_STATE_BLOCKED"
    if "secret" in message or "redaction" in message:
        return "SECRET_REDACTION_STATE_BLOCKED"
    if "private" in message or "access rights" in message:
        return "PRIVATE_DOC_ACCESS_RIGHTS_BLOCKED"
    if "source authority" in message or "source class" in message:
        return "SOURCE_AUTHORITY_CLASS_BLOCKED"
    if "locator" in message:
        return "SOURCE_LOCATOR_INVALID"
    return "CANDIDATE_VALIDATION_FAILED"


def _decision_ids(candidate: Mapping[str, Any]) -> tuple[str, str, str, str]:
    seed = {
        "candidate_source_evidence_packet_id": candidate.get(
            "candidate_source_evidence_packet_id", "UNKNOWN_CANDIDATE"
        ),
        "target_field_path": candidate.get("target_field_path", "UNKNOWN_TARGET"),
        "retrieval_manifest_id": candidate.get("retrieval_manifest_id", "UNKNOWN_MANIFEST"),
    }
    digest = canonical_digest(seed)[:24].upper()
    return (
        f"PR123_ACCEPTANCE_DECISION_{digest}",
        f"PR123_ACCEPTED_PACKET_{digest}",
        f"PR123_ACCEPTED_LEDGER_{digest}",
        f"PR123_REJECT_RECEIPT_{digest}",
    )


def validate_candidate_packet(candidate: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
    if missing:
        failures.append("candidate packet missing fields: " + ", ".join(missing))
        return failures

    if candidate.get("candidate_source_evidence_packet_record_type") != (
        "CANDIDATE_SOURCE_EVIDENCE_PACKET"
    ):
        failures.append("candidate packet record type must be CANDIDATE_SOURCE_EVIDENCE_PACKET")

    fixture = _candidate_is_fixture(candidate)
    if fixture and candidate.get("production_external_fact_authority") is not False:
        failures.append("fixture candidate production_external_fact_authority must be false")
    if fixture and candidate.get("source_authority_class") not in SOURCE_CLASSES:
        failures.append("fixture candidate source authority class is invalid")
    if not fixture and candidate.get("source_authority_class") not in OFFICIAL_SOURCE_CLASSES:
        failures.append("production candidate source authority class must be official")

    venue = candidate.get("venue_id")
    platform_scope = candidate.get("platform_scope")
    if venue not in ACTIVE_STAGE1_PLATFORM_SCOPES:
        failures.append("venue_id must be an active Stage-1 platform scope")
    if platform_scope not in ACTIVE_STAGE1_PLATFORM_SCOPES:
        failures.append("platform_scope must be an active Stage-1 platform scope")
    if venue in {"*", "ALL", "ANY"} or platform_scope in {"*", "ALL", "ANY"}:
        failures.append("wildcard venue/platform scope is forbidden")
    if venue in FUTURE_MARKET_FAMILIES or platform_scope in FUTURE_MARKET_FAMILIES:
        failures.append("future market family cannot be accepted in Stage-1 PR106")

    target_field_path = candidate.get("target_field_path")
    _validate_target_field_path(target_field_path, "target_field_path", failures)
    authorized_paths = candidate.get("target_field_paths_authorized")
    if not isinstance(authorized_paths, list) or not authorized_paths:
        failures.append("target_field_paths_authorized must be a non-empty list")
    else:
        for index, path in enumerate(authorized_paths):
            _validate_target_field_path(path, f"target_field_paths_authorized[{index}]", failures)
        if target_field_path not in authorized_paths:
            failures.append("target_field_path must be declared in target_field_paths_authorized")

    scope = candidate.get("applicability_scope")
    if not isinstance(scope, Mapping):
        failures.append("applicability_scope must be an object")
    else:
        if scope.get("wildcard_scope_allowed") is not False:
            failures.append("applicability_scope wildcard_scope_allowed must be false")
        if scope.get("cross_venue_scope_allowed") is not False:
            failures.append("applicability_scope cross_venue_scope_allowed must be false")
        if scope.get("venue_id") != venue:
            failures.append("applicability_scope venue_id must match candidate venue_id")
        if scope.get("platform_scope") != platform_scope:
            failures.append("applicability_scope platform_scope must match candidate platform_scope")
        scope_paths = scope.get("target_field_paths")
        if not isinstance(scope_paths, list) or target_field_path not in scope_paths:
            failures.append("target_field_path must be declared in applicability_scope")
        elif any("*" in path for path in scope_paths if isinstance(path, str)):
            failures.append("applicability_scope target fields must not contain wildcards")

    locator_type = candidate.get("source_locator_type")
    if locator_type not in VALID_LOCATOR_TYPES:
        failures.append("source locator type is invalid")
    if not _is_non_empty_string(candidate.get("source_locator")):
        failures.append("source locator must be present")
    if not fixture and locator_type in PLACEHOLDER_LOCATOR_TYPES:
        failures.append("production candidate cannot accept placeholder or fixture locator")
    if fixture and locator_type not in {"PLACEHOLDER_NOT_FACTUAL_URL", "FIXTURE_ONLY"}:
        failures.append("fixture candidate locator must be typed as non-factual fixture placeholder")

    for field in (
        "source_access_method",
        "source_retrieval_method",
        "source_retrieved_at_utc",
        "accepted_value_label",
        "target_section_id",
        "conflict_check_id",
        "revalidation_trigger_id",
        "revalidation_due_at_or_event",
    ):
        if not _is_non_empty_string(candidate.get(field)):
            failures.append(f"{field} must be present")

    for field in (
        "raw_capture_digest_sha256",
        "canonical_text_digest_sha256",
        "source_digest_sha256",
    ):
        if not _is_sha256(candidate.get(field)):
            failures.append(f"{field} must be a sha256 digest")

    raw_capture_text = candidate.get("raw_capture_text")
    if isinstance(raw_capture_text, str) and text_digest(raw_capture_text) != candidate.get(
        "raw_capture_digest_sha256"
    ):
        failures.append("raw_capture_digest_sha256 does not match raw_capture_text")
    canonical_text = candidate.get("canonical_text")
    if isinstance(canonical_text, str) and text_digest(canonical_text) != candidate.get(
        "canonical_text_digest_sha256"
    ):
        failures.append("canonical_text_digest_sha256 does not match canonical_text")
    if _is_sha256(candidate.get("raw_capture_digest_sha256")) and _is_sha256(
        candidate.get("canonical_text_digest_sha256")
    ):
        expected_source_digest = text_digest(
            f"{candidate['raw_capture_digest_sha256']}:{candidate['canonical_text_digest_sha256']}"
        )
        if candidate.get("source_digest_sha256") != expected_source_digest:
            failures.append("source_digest_sha256 does not match raw/canonical digest pair")

    locator_kind = candidate.get("quote_span_locator_or_machine_field_locator")
    exact_locator = candidate.get("exact_quote_or_machine_field_locator")
    if locator_kind not in {"QUOTE_SPAN_LOCATOR", "MACHINE_FIELD_LOCATOR"}:
        failures.append("quote_span_locator_or_machine_field_locator is invalid")
    if not isinstance(exact_locator, Mapping):
        failures.append("exact_quote_or_machine_field_locator must be an object")
    elif locator_kind == "QUOTE_SPAN_LOCATOR" and not isinstance(
        exact_locator.get("quote_span_locator"), Mapping
    ):
        failures.append("quote span locator payload is required")
    elif locator_kind == "MACHINE_FIELD_LOCATOR" and not isinstance(
        exact_locator.get("machine_field_locator"), Mapping
    ):
        failures.append("machine field locator payload is required")

    if candidate.get("extracted_fact_type") not in VALID_EXTRACTED_FACT_TYPES:
        failures.append("extracted_fact_type is invalid")
    if "extracted_fact_payload" not in candidate or "extracted_fact" not in candidate:
        failures.append("extracted fact payload and extracted fact must be present")

    if candidate.get("conflict_state") not in VALID_CONFLICT_STATES:
        failures.append("conflict_state blocks acceptance")
    if candidate.get("conflict_resolution_state") not in VALID_CONFLICT_RESOLUTION_STATES:
        failures.append("conflict_resolution_state blocks acceptance")

    if candidate.get("revalidation_trigger") not in VALID_REVALIDATION_TRIGGERS:
        failures.append("revalidation_trigger is invalid")
    if candidate.get("revalidation_state") not in FRESH_REVALIDATION_STATES:
        failures.append("stale revalidation state blocks acceptance")
    if candidate.get("revalidation_due_condition") not in FRESH_REVALIDATION_DUE_CONDITIONS:
        failures.append("revalidation_due_condition blocks acceptance")

    if candidate.get("redaction_state") not in SAFE_REDACTION_STATES:
        failures.append("redaction state blocks acceptance")
    if candidate.get("secret_like_value_detected_flag") is True and candidate.get(
        "redaction_state"
    ) != "REDACTED_SECRET_ALIAS_ONLY":
        failures.append("secret-like values must be redacted before acceptance")
    if _has_secret_like_value(candidate):
        failures.append("secret-like value detected in candidate")

    if candidate.get("private_doc_access_rights_state") not in SAFE_PRIVATE_DOC_STATES:
        failures.append("private document access rights are unclear")
    if locator_type == "OWNER_UPLOADED_PRIVATE_DOC_LOCATOR" and candidate.get(
        "private_doc_access_rights_state"
    ) != "OWNER_UPLOADED_PRIVATE_DOC_ACCESS_RIGHTS_ATTESTED":
        failures.append("private document locator requires owner access-rights attestation")

    for field in (
        "no_connector_semantic_population_flag",
        "no_live_reachability_flag",
        "no_order_execution_flag",
        "no_runtime_cash_claim_flag",
        "no_blocker_reduction_or_profit_claim_flag",
    ):
        if candidate.get(field) is not True:
            failures.append(f"{field} must be true")
    _validate_no_claim_flags(candidate.get("no_claim_flags"), "no_claim_flags", failures)

    if not isinstance(candidate.get("supersedes_packet_ids"), list):
        failures.append("supersedes_packet_ids must be a list")

    return failures


def _conflict_report(candidate: Mapping[str, Any], blocked: bool) -> dict[str, Any]:
    return {
        "source_acceptance_conflict_report_record_type": "SOURCE_ACCEPTANCE_CONFLICT_REPORT",
        "conflict_check_id": str(candidate.get("conflict_check_id", "UNKNOWN_CONFLICT_CHECK")),
        "candidate_source_evidence_packet_id": str(
            candidate.get("candidate_source_evidence_packet_id", "UNKNOWN_CANDIDATE")
        ),
        "target_field_path": str(candidate.get("target_field_path", "UNKNOWN_TARGET")),
        "conflict_state": str(candidate.get("conflict_state", "UNKNOWN_CONFLICT_STATE")),
        "conflict_resolution_state": str(
            candidate.get("conflict_resolution_state", "UNKNOWN_CONFLICT_RESOLUTION")
        ),
        "conflicting_packet_ids": list(candidate.get("conflicting_packet_ids", [])),
        "acceptance_blocked_by_conflict": blocked,
        "owner_or_risk_review_required": blocked,
        "connector_semantic_binding_allowed_flag": False,
        "runtime_live_use_allowed_flag": False,
    }


def _revalidation_status(candidate: Mapping[str, Any], blocked: bool) -> dict[str, Any]:
    return {
        "source_revalidation_status_record_type": "SOURCE_REVALIDATION_STATUS",
        "revalidation_trigger_id": str(
            candidate.get("revalidation_trigger_id", "UNKNOWN_REVALIDATION_TRIGGER")
        ),
        "candidate_source_evidence_packet_id": str(
            candidate.get("candidate_source_evidence_packet_id", "UNKNOWN_CANDIDATE")
        ),
        "target_field_path": str(candidate.get("target_field_path", "UNKNOWN_TARGET")),
        "revalidation_trigger": str(candidate.get("revalidation_trigger", "UNKNOWN")),
        "revalidation_due_at_or_event": str(
            candidate.get("revalidation_due_at_or_event", "UNKNOWN")
        ),
        "revalidation_due_condition": str(
            candidate.get("revalidation_due_condition", "UNKNOWN")
        ),
        "revalidation_state": str(candidate.get("revalidation_state", "UNKNOWN")),
        "acceptance_blocked_by_staleness": blocked,
        "fresh_revalidation_state_required_before_connector_binding": True,
        "connector_semantic_binding_allowed_flag": False,
        "runtime_live_use_allowed_flag": False,
    }


def _build_accepted_packet(
    candidate: Mapping[str, Any],
    decision_id: str,
    accepted_packet_id: str,
) -> dict[str, Any]:
    receipt_ids = [decision_id]
    return {
        "accepted_packet_record_type": "ACCEPTED_SOURCE_EVIDENCE_PACKET",
        "accepted_source_evidence_packet_id": accepted_packet_id,
        "accepted_source_evidence_packet_version": "PR106_ACCEPTED_SOURCE_EVIDENCE_PACKET_V1",
        "master_plan_edition": candidate["master_plan_edition"],
        "candidate_source_evidence_packet_id": candidate["candidate_source_evidence_packet_id"],
        "acceptance_decision_packet_id": decision_id,
        "retrieval_manifest_id": candidate["retrieval_manifest_id"],
        "source_target_id": candidate["source_target_id"],
        "retrieval_target_id": candidate["retrieval_target_id"],
        "venue_id": candidate["venue_id"],
        "platform_scope": candidate["platform_scope"],
        "source_locator": candidate["source_locator"],
        "source_locator_type": candidate["source_locator_type"],
        "source_locator_status": candidate["source_locator_status"],
        "source_authority_class": candidate["source_authority_class"],
        "source_access_method": candidate["source_access_method"],
        "source_retrieval_method": candidate["source_retrieval_method"],
        "source_retrieved_at_utc": candidate["source_retrieved_at_utc"],
        "raw_capture_digest_sha256": candidate["raw_capture_digest_sha256"],
        "canonical_text_digest_sha256": candidate["canonical_text_digest_sha256"],
        "source_digest_sha256": candidate["source_digest_sha256"],
        "quote_span_locator_or_machine_field_locator": candidate[
            "quote_span_locator_or_machine_field_locator"
        ],
        "exact_quote_or_machine_field_locator": candidate[
            "exact_quote_or_machine_field_locator"
        ],
        "extracted_fact_payload": candidate["extracted_fact_payload"],
        "extracted_fact_type": candidate["extracted_fact_type"],
        "extracted_fact": candidate["extracted_fact"],
        "accepted_value_label": candidate["accepted_value_label"],
        "target_section_id": candidate["target_section_id"],
        "target_field_paths_authorized": list(candidate["target_field_paths_authorized"]),
        "target_field_path": candidate["target_field_path"],
        "applicability_scope": dict(candidate["applicability_scope"]),
        "conflict_check_id": candidate["conflict_check_id"],
        "conflict_resolution_state": candidate["conflict_resolution_state"],
        "conflict_state": candidate["conflict_state"],
        "revalidation_trigger": candidate["revalidation_trigger"],
        "revalidation_trigger_id": candidate["revalidation_trigger_id"],
        "revalidation_due_at_or_event": candidate["revalidation_due_at_or_event"],
        "revalidation_due_condition": candidate["revalidation_due_condition"],
        "supersedes_packet_ids": list(candidate["supersedes_packet_ids"]),
        "accepted_at_utc": DETERMINISTIC_FIXTURE_TIMESTAMP,
        "accepted_by_tool": ACCEPTED_TOOL,
        "receipt_ids": receipt_ids,
        "production_external_fact_authority": bool(
            candidate.get("production_external_fact_authority")
        ),
        "no_connector_semantic_population_flag": True,
        "no_live_reachability_flag": True,
        "no_order_execution_flag": True,
        "no_runtime_cash_claim_flag": True,
        "no_blocker_reduction_or_profit_claim_flag": True,
        "no_claim_flags": default_no_claim_flags(),
    }


def _locator_pair(candidate: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    exact = candidate.get("exact_quote_or_machine_field_locator")
    if not isinstance(exact, Mapping):
        return None, None
    return exact.get("quote_span_locator"), exact.get("machine_field_locator")


def _build_ledger_record(
    candidate: Mapping[str, Any],
    accepted_packet: Mapping[str, Any],
    decision_id: str,
    ledger_id: str,
) -> dict[str, Any]:
    quote_span_locator, machine_field_locator = _locator_pair(candidate)
    return {
        "accepted_ledger_record_id": ledger_id,
        "accepted_source_evidence_packet_id": accepted_packet[
            "accepted_source_evidence_packet_id"
        ],
        "candidate_source_evidence_packet_id": candidate["candidate_source_evidence_packet_id"],
        "acceptance_decision_packet_id": decision_id,
        "retrieval_manifest_id": candidate["retrieval_manifest_id"],
        "source_target_id": candidate["source_target_id"],
        "retrieval_target_id": candidate["retrieval_target_id"],
        "venue_id": candidate["venue_id"],
        "platform_scope": candidate["platform_scope"],
        "target_field_path": candidate["target_field_path"],
        "applicability_scope": dict(candidate["applicability_scope"]),
        "accepted_value_type": candidate["extracted_fact_type"],
        "accepted_value_label": candidate["accepted_value_label"],
        "accepted_value_locator": candidate["quote_span_locator_or_machine_field_locator"],
        "quote_span_locator": quote_span_locator,
        "machine_field_locator": machine_field_locator,
        "canonicalized_content_digest": candidate["canonical_text_digest_sha256"],
        "canonical_text_digest_sha256": candidate["canonical_text_digest_sha256"],
        "source_digest_sha256": candidate["source_digest_sha256"],
        "source_class": candidate["source_authority_class"],
        "source_authority_class": candidate["source_authority_class"],
        "source_locator": candidate["source_locator"],
        "source_locator_type": candidate["source_locator_type"],
        "source_locator_status": candidate["source_locator_status"],
        "redaction_state": candidate["redaction_state"],
        "conflict_state": candidate["conflict_state"],
        "conflict_resolution_state": candidate["conflict_resolution_state"],
        "revalidation_state": candidate["revalidation_state"],
        "source_change_materiality_class": candidate["source_change_materiality_class"],
        "accepted_at_utc": DETERMINISTIC_FIXTURE_TIMESTAMP,
        "accepted_by_tool": ACCEPTED_TOOL,
        "receipt_ids": [decision_id],
        "acceptance_authority_state": "TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE_NONLIVE_ONLY",
        "acceptance_decision_receipt_ref": decision_id,
        "connector_semantic_unlock_candidate_flag": True,
        "connector_semantic_unlock_allowed_flag": False,
        "runtime_live_use_allowed_flag": False,
        "order_authority_allowed_flag": False,
        "profit_evidence_allowed_flag": False,
        "quantum_backend_execution_allowed_flag": False,
        "production_external_fact_authority": bool(
            candidate.get("production_external_fact_authority")
        ),
    }


def build_acceptance_artifacts(candidate: Mapping[str, Any]) -> ExecuteAcceptanceResult:
    failures = validate_candidate_packet(candidate)
    conflict_blocked = any("conflict" in failure for failure in failures)
    stale_blocked = any(
        "revalidation" in failure or "stale" in failure for failure in failures
    )
    conflict_report = _conflict_report(candidate, conflict_blocked)
    revalidation_status = _revalidation_status(candidate, stale_blocked)
    decision_id, accepted_packet_id, ledger_id, reject_receipt_id = _decision_ids(candidate)

    if failures:
        rejection_codes = sorted({_failure_code(failure) for failure in failures})
        reject_receipt = {
            "source_acceptance_reject_receipt_record_type": "SOURCE_ACCEPTANCE_REJECT_RECEIPT",
            "reject_receipt_id": reject_receipt_id,
            "candidate_source_evidence_packet_id": str(
                candidate.get("candidate_source_evidence_packet_id", "UNKNOWN_CANDIDATE")
            ),
            "rejection_codes": rejection_codes,
            "rejection_messages": failures,
            "accepted_source_evidence_packet_created": False,
            "accepted_ledger_record_created": False,
            "connector_semantic_binding_created": False,
            "runtime_live_authority_created": False,
            "order_authority_created": False,
            "profit_evidence_created": False,
            "quantum_backend_execution_created": False,
            "rejected_at_utc": DETERMINISTIC_FIXTURE_TIMESTAMP,
        }
        decision = {
            "acceptance_decision_receipt_record_type": (
                "SOURCE_EVIDENCE_ACCEPTANCE_DECISION_RECEIPT"
            ),
            "acceptance_decision_packet_id": decision_id,
            "decision": "REJECTED",
            "candidate_source_evidence_packet_id": str(
                candidate.get("candidate_source_evidence_packet_id", "UNKNOWN_CANDIDATE")
            ),
            "accepted_source_evidence_packet_id": None,
            "accepted_ledger_record_id": None,
            "target_field_path": str(candidate.get("target_field_path", "UNKNOWN_TARGET")),
            "rejection_codes": rejection_codes,
            "validation_failure_messages": failures,
            "conflict_report_ref": conflict_report["conflict_check_id"],
            "revalidation_status_ref": revalidation_status["revalidation_trigger_id"],
            "reject_receipt_ref": reject_receipt_id,
            "decided_at_utc": DETERMINISTIC_FIXTURE_TIMESTAMP,
            "decided_by_tool": ACCEPTED_TOOL,
            "production_external_fact_authority": False,
            "connector_semantic_binding_created_count": 0,
            "runtime_live_authority_created": False,
            "order_authority_created": False,
            "profit_evidence_created": False,
            "quantum_backend_execution_count": 0,
        }
        return ExecuteAcceptanceResult(
            decision_receipt=decision,
            accepted_packet=None,
            accepted_ledger_record=None,
            conflict_report=conflict_report,
            revalidation_status=revalidation_status,
            reject_receipt=reject_receipt,
        )

    accepted_packet = _build_accepted_packet(candidate, decision_id, accepted_packet_id)
    ledger_record = _build_ledger_record(candidate, accepted_packet, decision_id, ledger_id)
    decision = {
        "acceptance_decision_receipt_record_type": "SOURCE_EVIDENCE_ACCEPTANCE_DECISION_RECEIPT",
        "acceptance_decision_packet_id": decision_id,
        "decision": "ACCEPTED",
        "candidate_source_evidence_packet_id": candidate["candidate_source_evidence_packet_id"],
        "accepted_source_evidence_packet_id": accepted_packet_id,
        "accepted_ledger_record_id": ledger_id,
        "target_field_path": candidate["target_field_path"],
        "rejection_codes": [],
        "validation_failure_messages": [],
        "conflict_report_ref": conflict_report["conflict_check_id"],
        "revalidation_status_ref": revalidation_status["revalidation_trigger_id"],
        "reject_receipt_ref": None,
        "decided_at_utc": DETERMINISTIC_FIXTURE_TIMESTAMP,
        "decided_by_tool": ACCEPTED_TOOL,
        "production_external_fact_authority": bool(candidate.get("production_external_fact_authority")),
        "connector_semantic_binding_created_count": 0,
        "runtime_live_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_execution_count": 0,
    }
    return ExecuteAcceptanceResult(
        decision_receipt=decision,
        accepted_packet=accepted_packet,
        accepted_ledger_record=ledger_record,
        conflict_report=conflict_report,
        revalidation_status=revalidation_status,
        reject_receipt=None,
    )


def validate_accepted_packet(packet: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    missing = sorted(REQUIRED_ACCEPTED_PACKET_FIELDS - set(packet))
    if missing:
        failures.append("accepted packet missing fields: " + ", ".join(missing))
        return failures
    if packet.get("accepted_packet_record_type") != "ACCEPTED_SOURCE_EVIDENCE_PACKET":
        failures.append("accepted packet record type is invalid")
    if packet.get("accepted_source_evidence_packet_version") != (
        "PR106_ACCEPTED_SOURCE_EVIDENCE_PACKET_V1"
    ):
        failures.append("accepted packet version is invalid")
    for field in (
        "raw_capture_digest_sha256",
        "canonical_text_digest_sha256",
        "source_digest_sha256",
    ):
        if not _is_sha256(packet.get(field)):
            failures.append(f"accepted packet {field} must be sha256")
    if packet.get("target_field_path") not in packet.get("target_field_paths_authorized", []):
        failures.append("accepted packet target_field_path must be authorized")
    for field in (
        "no_connector_semantic_population_flag",
        "no_live_reachability_flag",
        "no_order_execution_flag",
        "no_runtime_cash_claim_flag",
        "no_blocker_reduction_or_profit_claim_flag",
    ):
        if packet.get(field) is not True:
            failures.append(f"accepted packet {field} must be true")
    _validate_no_claim_flags(packet.get("no_claim_flags"), "accepted packet no_claim_flags", failures)
    return failures


def validate_ledger_record(record: Mapping[str, Any]) -> list[str]:
    required = {
        "accepted_ledger_record_id",
        "accepted_source_evidence_packet_id",
        "candidate_source_evidence_packet_id",
        "acceptance_decision_packet_id",
        "retrieval_manifest_id",
        "source_target_id",
        "retrieval_target_id",
        "venue_id",
        "platform_scope",
        "target_field_path",
        "applicability_scope",
        "accepted_value_type",
        "accepted_value_label",
        "accepted_value_locator",
        "quote_span_locator",
        "machine_field_locator",
        "canonicalized_content_digest",
        "canonical_text_digest_sha256",
        "source_digest_sha256",
        "source_class",
        "source_authority_class",
        "source_locator",
        "source_locator_type",
        "source_locator_status",
        "redaction_state",
        "conflict_state",
        "conflict_resolution_state",
        "revalidation_state",
        "source_change_materiality_class",
        "accepted_at_utc",
        "accepted_by_tool",
        "receipt_ids",
        "acceptance_authority_state",
        "acceptance_decision_receipt_ref",
        "connector_semantic_unlock_candidate_flag",
        "connector_semantic_unlock_allowed_flag",
        "runtime_live_use_allowed_flag",
        "order_authority_allowed_flag",
        "profit_evidence_allowed_flag",
        "quantum_backend_execution_allowed_flag",
        "production_external_fact_authority",
    }
    failures: list[str] = []
    missing = sorted(required - set(record))
    if missing:
        failures.append("accepted ledger record missing fields: " + ", ".join(missing))
        return failures
    _validate_target_field_path(record.get("target_field_path"), "ledger target_field_path", failures)
    for field in (
        "canonicalized_content_digest",
        "canonical_text_digest_sha256",
        "source_digest_sha256",
    ):
        if not _is_sha256(record.get(field)):
            failures.append(f"accepted ledger {field} must be sha256")
    for field in (
        "connector_semantic_unlock_allowed_flag",
        "runtime_live_use_allowed_flag",
        "order_authority_allowed_flag",
        "profit_evidence_allowed_flag",
        "quantum_backend_execution_allowed_flag",
    ):
        if record.get(field) is not False:
            failures.append(f"accepted ledger {field} must be false")
    if record.get("acceptance_authority_state") != (
        "TARGET_FIELD_ACCEPTED_SOURCE_EVIDENCE_NONLIVE_ONLY"
    ):
        failures.append("accepted ledger authority state is invalid")
    return failures


def validate_decision_receipt(receipt: Mapping[str, Any]) -> list[str]:
    required = {
        "acceptance_decision_receipt_record_type",
        "acceptance_decision_packet_id",
        "decision",
        "candidate_source_evidence_packet_id",
        "accepted_source_evidence_packet_id",
        "accepted_ledger_record_id",
        "target_field_path",
        "rejection_codes",
        "validation_failure_messages",
        "conflict_report_ref",
        "revalidation_status_ref",
        "reject_receipt_ref",
        "decided_at_utc",
        "decided_by_tool",
        "production_external_fact_authority",
        "connector_semantic_binding_created_count",
        "runtime_live_authority_created",
        "order_authority_created",
        "profit_evidence_created",
        "quantum_backend_execution_count",
    }
    failures: list[str] = []
    missing = sorted(required - set(receipt))
    if missing:
        failures.append("acceptance decision receipt missing fields: " + ", ".join(missing))
        return failures
    if receipt.get("acceptance_decision_receipt_record_type") != (
        "SOURCE_EVIDENCE_ACCEPTANCE_DECISION_RECEIPT"
    ):
        failures.append("acceptance decision receipt record type is invalid")
    if receipt.get("decision") not in {"ACCEPTED", "REJECTED"}:
        failures.append("acceptance decision must be ACCEPTED or REJECTED")
    if receipt.get("decision") == "ACCEPTED":
        if receipt.get("rejection_codes") or receipt.get("validation_failure_messages"):
            failures.append("accepted decision must not contain rejection details")
        if not receipt.get("accepted_source_evidence_packet_id"):
            failures.append("accepted decision must reference accepted packet")
        if not receipt.get("accepted_ledger_record_id"):
            failures.append("accepted decision must reference accepted ledger record")
    if receipt.get("decision") == "REJECTED":
        if not receipt.get("rejection_codes"):
            failures.append("rejected decision must contain rejection codes")
        if receipt.get("accepted_source_evidence_packet_id") is not None:
            failures.append("rejected decision must not reference accepted packet")
        if receipt.get("accepted_ledger_record_id") is not None:
            failures.append("rejected decision must not reference ledger record")
    if receipt.get("connector_semantic_binding_created_count") != 0:
        failures.append("decision receipt must not create connector semantic binding")
    for field in (
        "runtime_live_authority_created",
        "order_authority_created",
        "profit_evidence_created",
    ):
        if receipt.get(field) is not False:
            failures.append(f"decision receipt {field} must be false")
    if receipt.get("quantum_backend_execution_count") != 0:
        failures.append("decision receipt must not create quantum backend execution")
    return failures
