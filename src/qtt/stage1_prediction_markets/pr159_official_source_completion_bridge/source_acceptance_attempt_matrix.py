"""Per-target PR159 second-pass acceptance-attempt matrix."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _candidate_by_target(candidate_packets: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {
        str(packet["target_id_or_row_id"]): packet
        for packet in sorted(candidate_packets, key=lambda item: str(item["candidate_packet_id"]))
    }


def _accepted_by_candidate(accepted_packets: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(packet["candidate_packet_id"]): packet for packet in accepted_packets}


def _target_key(target: Mapping[str, Any]) -> str:
    if target.get("row_id"):
        return str(target["row_id"])
    return str(target["target_id"])


def _blocker_reason(target: Mapping[str, Any], candidate: Mapping[str, Any] | None) -> str:
    if candidate is None:
        return c.SourceEvidenceState.BLOCKED_NO_OFFICIAL_SOURCE.value
    if not candidate.get("target_field_scope_match_flag"):
        return c.SourceEvidenceState.BLOCKED_TARGET_FIELD_SCOPE_MISMATCH.value
    if candidate.get("extracted_value_or_range_or_enum_or_null") is None:
        return c.SourceEvidenceState.BLOCKED_AMBIGUOUS.value
    if not candidate.get("extracted_unit_or_basis_or_null") or not candidate.get("extracted_scale_or_null"):
        return c.SourceEvidenceState.BLOCKED_UNIT_SCALE_CANONICALIZATION.value
    if candidate.get("conflict_clearance_status") != c.ConflictStatus.NO_CONFLICT.value:
        return c.SourceEvidenceState.BLOCKED_CONFLICTING_OFFICIAL_SOURCES.value
    return c.SourceEvidenceState.BLOCKED_SCHEMA_INVALID.value


def _next_action(target: Mapping[str, Any], candidate: Mapping[str, Any] | None, accepted: bool) -> str:
    if accepted:
        return "Accepted from exact official target-field evidence; no second-pass source action remains."
    if target.get("source_population") == c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value:
        source_hint = ", ".join(str(ref) for ref in target.get("discovered_official_source_refs", []))
        if not source_hint:
            source_hint = "an official source matching the target platform"
        return (
            f"Capture an exact official value/range/enum and canonical unit/scale for "
            f"{target['platform_scope']} {target['target_field_id']} from {source_hint}; "
            "then rerun PR159 acceptance validation."
        )
    return (
        f"Create a row-specific official source packet for {target['target_field_id']} with "
        "an exact value/range/constraint, locator, unit, scale, freshness state, and conflict clearance."
    )


def build_source_acceptance_attempt_matrix(
    target_queue: list[Mapping[str, Any]],
    candidate_packets: list[Mapping[str, Any]],
    accepted_packets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates = _candidate_by_target(candidate_packets)
    accepted_by_candidate = _accepted_by_candidate(accepted_packets)
    records: list[dict[str, Any]] = []
    for target in target_queue:
        target_id_or_row_id = _target_key(target)
        candidate = candidates.get(str(target.get("target_id")))
        accepted_packet = None
        if candidate is not None:
            accepted_packet = accepted_by_candidate.get(str(candidate.get("candidate_packet_id")))
        accepted = accepted_packet is not None
        locator = candidate.get("quote_span_or_machine_field_locator") if candidate else {}
        locator_available = bool(
            accepted
            and isinstance(locator, Mapping)
            and locator.get("locator")
            and (locator.get("quote_span") or locator.get("machine_field_locator"))
        )
        exact_target_match = bool(accepted and candidate and candidate.get("target_field_scope_match_flag"))
        exact_value_available = bool(accepted and candidate.get("extracted_value_or_range_or_enum_or_null") is not None)
        exact_unit_scale_available = bool(
            accepted and candidate.get("extracted_unit_or_basis_or_null") and candidate.get("extracted_scale_or_null")
        )
        freshness_available = bool(
            candidate
            and candidate.get("freshness_state")
            in {
                c.FreshnessState.FRESH.value,
                c.FreshnessState.REVALIDATION_NOT_APPLICABLE_METADATA_ONLY.value,
            }
        )
        conflict_possible = bool(candidate and candidate.get("conflict_clearance_status") == c.ConflictStatus.NO_CONFLICT.value)
        acceptance_possible = bool(
            exact_target_match
            and exact_value_available
            and exact_unit_scale_available
            and locator_available
            and freshness_available
            and conflict_possible
        )
        attempted_refs = []
        if candidate is not None:
            attempted_refs.append(str(candidate.get("official_source_ref")))
        attempted_refs.extend(str(ref) for ref in target.get("discovered_official_source_refs", []) if ref)
        attempted_refs = sorted(set(attempted_refs))
        records.append(
            {
                "target_id_or_row_id": target_id_or_row_id,
                "target_field_id": target["target_field_id"],
                "source_requirement_class": target.get("source_requirement_class", "PR154_PUBLIC_SOURCE_RETRY_REQUIRED"),
                "day1_priority_tier": target["day1_source_priority_tier"],
                "attempted_source_refs": attempted_refs,
                "exact_target_field_match_flag": exact_target_match,
                "exact_value_available_flag": exact_value_available,
                "exact_unit_scale_available_flag": exact_unit_scale_available,
                "exact_locator_available_flag": locator_available,
                "freshness_available_flag": freshness_available,
                "conflict_clearance_possible_flag": conflict_possible,
                "acceptance_possible_flag": acceptance_possible,
                "acceptance_blocker_reason": None if accepted else _blocker_reason(target, candidate),
                "accepted_packet_ref_or_null": (
                    accepted_packet.get("accepted_packet_id") if accepted_packet else None
                ),
                "exact_next_action": _next_action(target, candidate, accepted),
            }
        )
    return sorted(records, key=lambda item: str(item["target_id_or_row_id"]))

