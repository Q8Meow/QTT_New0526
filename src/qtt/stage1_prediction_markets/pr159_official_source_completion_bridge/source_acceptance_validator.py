"""Fail-closed acceptance validation helpers for PR159 candidate packets."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def validate_candidate_for_acceptance(candidate: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if candidate.get("official_source_confidence") != c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value:
        failures.append(c.SourceEvidenceState.BLOCKED_SOURCE_NOT_OFFICIAL.value)
    if not candidate.get("target_field_scope_match_flag"):
        failures.append(c.SourceEvidenceState.BLOCKED_TARGET_FIELD_SCOPE_MISMATCH.value)
    locator = candidate.get("quote_span_or_machine_field_locator")
    if not isinstance(locator, Mapping) or not locator.get("locator") or not locator.get("quote_span"):
        failures.append(c.SourceEvidenceState.BLOCKED_QUOTE_OR_LOCATOR_MISSING.value)
    if candidate.get("freshness_state") in {
        c.FreshnessState.STALE.value,
        c.FreshnessState.SUPERSEDED.value,
        c.FreshnessState.VERSION_UNKNOWN.value,
    }:
        failures.append(c.SourceEvidenceState.BLOCKED_STALE_OR_REVALIDATION_REQUIRED.value)
    if candidate.get("extracted_value_or_range_or_enum_or_null") is None:
        failures.append(c.SourceEvidenceState.BLOCKED_AMBIGUOUS.value)
    if not candidate.get("extracted_unit_or_basis_or_null") or not candidate.get("extracted_scale_or_null"):
        failures.append(c.SourceEvidenceState.BLOCKED_UNIT_SCALE_CANONICALIZATION.value)
    if candidate.get("conflict_clearance_status") != c.ConflictStatus.NO_CONFLICT.value:
        failures.append(c.SourceEvidenceState.BLOCKED_CONFLICTING_OFFICIAL_SOURCES.value)
    return {
        "candidate_packet_id": candidate.get("candidate_packet_id"),
        "validated": not failures,
        "acceptance_decision": (
            c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_EXACT.value
            if not failures
            else c.SourceAcceptanceDecision.DEFERRED_FUTURE_SOURCE_RETRY.value
        ),
        "failure_codes": sorted(set(failures)),
        "accepted_fact_created": False,
    }


def build_accepted_packets(candidate_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for packet in candidate_packets:
        result = validate_candidate_for_acceptance(packet)
        if not result["validated"]:
            continue
        accepted.append(
            {
                "accepted_packet_id": f"PR159_ACCEPTED_PACKET__{packet['candidate_packet_id']}",
                "candidate_packet_id": packet["candidate_packet_id"],
                "target_id_or_row_id": packet["target_id_or_row_id"],
                "target_field_id": packet["target_field_id"],
                "source_population": packet["source_population"],
                "source_requirement_class": packet["source_requirement_class"],
                "source_url_or_repo_relative_capture_path": packet["source_url_or_repo_relative_capture_path"],
                "official_source_ref": packet["official_source_ref"],
                "quote_span_or_machine_field_locator": packet["quote_span_or_machine_field_locator"],
                "freshness_state": packet["freshness_state"],
                "accepted_value_or_range_or_enum": packet["extracted_value_or_range_or_enum_or_null"],
                "canonical_unit_or_basis": packet["extracted_unit_or_basis_or_null"],
                "canonical_scale": packet["extracted_scale_or_null"],
                "official_source_class": packet["official_source_class"],
                "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
                "target_field_scope_match_flag": True,
                "locator_valid_flag": True,
                "conflict_cleared_flag": True,
                "freshness_valid_flag": True,
                "unit_scale_canonicalized_flag": True,
                "acceptance_decision": result["acceptance_decision"],
                "acceptance_validator_id": "tools/validate_pr159_official_source_completion_bridge.py",
                "revalidation_class": packet["revalidation_class"],
                "materiality_class": packet["materiality_class"],
                "downstream_consumer_scope": "PR159_STATIC_SOURCE_READINESS_METADATA_ONLY",
                "no_connector_semantic_binding_confirmation": True,
                "no_runtime_receipt_confirmation": True,
                "no_live_order_authority_confirmation": True,
                "no_profit_evidence_confirmation": True,
            }
        )
    return accepted
