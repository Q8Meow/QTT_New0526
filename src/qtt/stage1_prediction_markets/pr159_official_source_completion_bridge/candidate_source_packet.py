"""Candidate source-evidence packet construction for PR159."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .io import safe_id
from .official_source_discovery import official_source_by_ref
from .second_pass_source_evidence import exact_evidence_for_target


def build_candidate_packets(target_queue: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    sources = official_source_by_ref()
    packets: list[dict[str, Any]] = []
    for target in target_queue:
        if target.get("source_population") != c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value:
            continue
        refs = target.get("discovered_official_source_refs")
        if not isinstance(refs, list) or not refs:
            continue
        exact_evidence = exact_evidence_for_target(target)
        source_ref = str(exact_evidence["official_source_ref"]) if exact_evidence else str(refs[0])
        source = sources[source_ref]
        target_id = str(target["target_id"])
        packet_id = f"PR159_CANDIDATE_PACKET__{safe_id(target_id)}"
        locator_type = str(exact_evidence["locator_type"]) if exact_evidence else source["locator_type"]
        locator = str(exact_evidence["locator"]) if exact_evidence else source["locator"]
        quote_span = str(exact_evidence["quote_span"]) if exact_evidence else source["quote_span"]
        extracted_value = exact_evidence["accepted_value_or_range_or_enum"] if exact_evidence else None
        extracted_unit = (
            str(exact_evidence["canonical_unit_or_basis"]) if exact_evidence else source["canonical_unit_or_basis"]
        )
        extracted_scale = str(exact_evidence["canonical_scale"]) if exact_evidence else source["canonical_scale"]
        target_field_scope_match = exact_evidence is not None
        packets.append(
            {
                "candidate_packet_id": packet_id,
                "target_id_or_row_id": target_id,
                "target_field_id": target["target_field_id"],
                "source_population": target["source_population"],
                "source_requirement_class": target.get("source_requirement_class", "PR154_PUBLIC_SOURCE_RETRY_REQUIRED"),
                "source_url_or_repo_relative_capture_path": source["source_url"],
                "official_source_ref": source["official_source_ref"],
                "official_source_class": source["official_source_class"],
                "official_source_confidence": source["official_source_confidence"],
                "non_authoritative_seed_ref_or_null": None,
                "platform_scope": target["platform_scope"],
                "venue_scope": target["platform_scope"],
                "market_scope": target["market_scope"],
                "source_title": source["source_title"],
                "source_publisher": source["source_publisher"],
                "source_version_or_date_or_null": source["source_version_or_date_or_null"],
                "retrieval_timestamp_utc": c.OFFICIAL_SEARCH_RETRIEVAL_TIMESTAMP_UTC,
                "retrieval_method": c.OFFICIAL_SEARCH_METHOD,
                "source_content_type": "text/html" if not source["source_url"].endswith(".pdf") else "application/pdf",
                "locator_type": locator_type,
                "quote_span_or_machine_field_locator": {
                    "locator": locator,
                    "quote_span": quote_span,
                },
                "extracted_value_or_range_or_enum_or_null": extracted_value,
                "extracted_unit_or_basis_or_null": extracted_unit,
                "extracted_scale_or_null": extracted_scale,
                "extraction_confidence_class": (
                    "EXACT_TARGET_FIELD_OFFICIAL_SOURCE_EXTRACTED"
                    if exact_evidence
                    else "CANDIDATE_CONTEXT_ONLY_SCOPE_NOT_ACCEPTED"
                ),
                "freshness_state": (
                    str(exact_evidence["freshness_state"]) if exact_evidence else source["freshness_state"]
                ),
                "conflict_clearance_status": (
                    str(exact_evidence["conflict_clearance_status"])
                    if exact_evidence
                    else c.ConflictStatus.CONFLICT_WITH_TARGET_FIELD_SCOPE.value
                ),
                "revalidation_class": (
                    str(exact_evidence["revalidation_class"]) if exact_evidence else target["revalidation_class"]
                ),
                "materiality_class": (
                    str(exact_evidence["materiality_class"]) if exact_evidence else target["source_materiality_class"]
                ),
                "provenance_digest_or_null": None,
                "candidate_is_accepted_fact": False,
                "target_field_scope_match_flag": target_field_scope_match,
                "candidate_validation_state": (
                    str(exact_evidence["candidate_validation_state"])
                    if exact_evidence
                    else c.SourceEvidenceState.BLOCKED_TARGET_FIELD_SCOPE_MISMATCH.value
                ),
                "acceptance_decision": (
                    str(exact_evidence["acceptance_decision"])
                    if exact_evidence
                    else c.SourceAcceptanceDecision.DEFERRED_FUTURE_SOURCE_RETRY.value
                ),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(packets, key=lambda item: item["candidate_packet_id"])


def candidate_refs_by_target(packets: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for packet in packets:
        target = str(packet.get("target_id_or_row_id"))
        refs.setdefault(target, []).append(str(packet.get("candidate_packet_id")))
    return {key: sorted(value) for key, value in refs.items()}
