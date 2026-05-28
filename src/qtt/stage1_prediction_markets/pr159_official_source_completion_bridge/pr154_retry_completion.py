"""PR154 34-record public-source retry completion records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_pr154_completion_records(
    pr154_targets: list[Mapping[str, Any]],
    candidate_refs_by_target: dict[str, list[str]],
    accepted_by_candidate: dict[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in pr154_targets:
        target_id = str(target["target_id"])
        candidate_refs = candidate_refs_by_target.get(target_id, [])
        accepted_packet = next(
            (accepted_by_candidate[ref] for ref in candidate_refs if ref in accepted_by_candidate),
            None,
        )
        completed = accepted_packet is not None
        records.append(
            {
                "target_id": target_id,
                "source_population": target["source_population"],
                "retry_source_ref": target["retry_source_ref"],
                "prior_PR153R_ref_or_null": target["prior_PR153R_ref_or_null"],
                "target_field_id": target["target_field_id"],
                "requested_value_name": target["requested_value_name"],
                "requested_value_type": target["requested_value_type"],
                "requested_unit_or_basis": target["requested_unit_or_basis"],
                "requested_scale": target["requested_scale"],
                "platform_scope": target["platform_scope"],
                "market_scope": target["market_scope"],
                "day1_source_priority_tier": target["day1_source_priority_tier"],
                "official_source_target_ids": target["official_source_target_ids"],
                "discovered_official_source_refs": target["discovered_official_source_refs"],
                "candidate_packet_refs": candidate_refs,
                "accepted_source_packet_ref_or_null": accepted_packet.get("accepted_packet_id") if accepted_packet else None,
                "acceptance_decision": (
                    accepted_packet["acceptance_decision"]
                    if accepted_packet
                    else c.SourceAcceptanceDecision.DEFERRED_FUTURE_SOURCE_RETRY.value
                ),
                "accepted_value_or_null": accepted_packet.get("accepted_value_or_range_or_enum") if accepted_packet else None,
                "value_canonicalization_ref_or_null": accepted_packet.get("accepted_packet_id") if accepted_packet else None,
                "quote_span_or_machine_field_locator_or_null": (
                    accepted_packet.get("quote_span_or_machine_field_locator") if accepted_packet else None
                ),
                "conflict_clearance_status": c.ConflictStatus.NO_CONFLICT.value,
                "freshness_state": (
                    accepted_packet.get("freshness_state")
                    if accepted_packet
                    else c.FreshnessState.EVENT_REVALIDATION_REQUIRED.value
                ),
                "revalidation_class": target["revalidation_class"],
                "materiality_class": target["source_materiality_class"],
                "completion_status": (
                    c.SourceTargetState.ACCEPTED_COMPLETED.value
                    if completed
                    else c.SourceTargetState.CANDIDATE_ONLY.value
                ),
                "blocker_class": None if completed else c.SourceTargetState.BLOCKED_AMBIGUOUS_SCOPE.value,
                "exact_next_action_if_unresolved": None
                if completed
                else "Promote only after a PR159/PR160 successor captures an exact target-field locator, value, unit, scale, freshness, and conflict clearance.",
                "future_route": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["target_id"])
