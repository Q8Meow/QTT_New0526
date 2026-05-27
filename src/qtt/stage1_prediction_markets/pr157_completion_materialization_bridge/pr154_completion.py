"""PR154 342-target completion bridge."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from . import constants as c
from . import owner_editability
from .agent_responsibility_bridge import for_pr154_record as agent_for_pr154_record
from .io import stable_counter_from_records, text
from .private_doc_attestation import attestation_request_id
from .source_authority_state import pr154_authority_class, source_locator, source_packet_ref
from .split_reclassification import reclassification_request_id


LANE_TO_POPULATION = {
    "PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE": (
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value
    ),
    "PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE": (
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value
    ),
    "INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE": (
        c.SourcePopulation.PR154_INTERNAL_CONTROL_PLANE.value
    ),
    "SPLIT_OR_RECLASSIFICATION_REQUIRED": (
        c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value
    ),
    "PRIVATE_DOC_ATTESTATION_REQUIRED": (
        c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value
    ),
    "OWNER_PROVIDED_ROUTE_REQUIRED": c.SourcePopulation.PR154_OWNER_ROUTE.value,
}


def source_population(record: Mapping[str, Any]) -> str:
    return LANE_TO_POPULATION.get(
        text(record.get("pr153s_closure_lane")),
        c.SourcePopulation.PR154_OWNER_ROUTE.value,
    )


def _completion_class(record: Mapping[str, Any], population: str) -> str:
    complete = bool(record.get("materialization_allowed"))
    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value:
        return (
            c.CompletionClass.PUBLIC_EXTERNAL_CAPTURED_COMPLETED_FROM_EXISTING_ACCEPTED_EVIDENCE.value
            if complete
            else c.CompletionClass.PUBLIC_EXTERNAL_CAPTURED_STILL_BLOCKED.value
        )
    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value:
        return (
            c.CompletionClass.PUBLIC_EXTERNAL_RETRY_EVIDENCE_ALREADY_PRESENT_COMPLETED.value
            if complete
            else c.CompletionClass.PUBLIC_EXTERNAL_RETRY_STILL_BLOCKED_FOR_FUTURE_SOURCE_RETRY_PR.value
        )
    if population == c.SourcePopulation.PR154_INTERNAL_CONTROL_PLANE.value:
        return (
            c.CompletionClass.INTERNAL_CONTROL_PLANE_COMPLETED.value
            if complete
            else c.CompletionClass.INTERNAL_CONTROL_PLANE_OWNER_INPUT_REQUIRED.value
        )
    if population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
        return (
            c.CompletionClass.SPLIT_RECLASSIFIED_COMPLETED.value
            if complete
            else c.CompletionClass.SPLIT_RECLASSIFICATION_OWNER_DECISION_REQUIRED.value
        )
    if population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
        return (
            c.CompletionClass.PRIVATE_DOC_ATTESTED_COMPLETED.value
            if complete
            else c.CompletionClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
        )
    return (
        c.CompletionClass.OWNER_ROUTE_COMPLETED.value
        if complete
        else c.CompletionClass.OWNER_ROUTE_INPUT_REQUIRED.value
    )


def _blocker_class(population: str, complete: bool) -> str:
    if complete:
        return c.BlockerClass.NONE.value
    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value:
        return c.BlockerClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value
    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value:
        return c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value
    if population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
        return c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
    if population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
        return c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value
    return c.BlockerClass.OWNER_INPUT_REQUIRED.value


def _future_route(population: str, complete: bool) -> str:
    if complete:
        return "NONE_VALUE_ALREADY_MATERIALIZED"
    if population in {
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
    }:
        return c.FutureEligibility.ELIGIBLE_FOR_PUBLIC_RETRY_PR159.value
    if population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
        return c.FutureEligibility.ELIGIBLE_FOR_SPLIT_RECLASSIFICATION_PR160.value
    return c.FutureEligibility.ELIGIBLE_FOR_OWNER_INPUT_PR158.value


def _owner_request_id(record_id: str, population: str, complete: bool) -> str | None:
    if complete:
        return None
    if population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
        return attestation_request_id(record_id)
    if population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
        return reclassification_request_id(record_id)
    if population == c.SourcePopulation.PR154_OWNER_ROUTE.value:
        return f"PR157_OWNER_ROUTE_REQUEST__{record_id}"
    return None


def _fill_plan_ref(record: Mapping[str, Any], blocker: str, future_route: str) -> list[dict[str, Any]]:
    if blocker == c.BlockerClass.NONE.value:
        return []
    record_id = text(record.get("pr154_record_id"))
    return [
        {
            "fill_plan_id": f"PR157_PR154_FILL_PLAN__{record_id}",
            "blocker_class": blocker,
            "fill_route_class": (
                c.FillRouteClass.FILL_AFTER_PUBLIC_SOURCE_RETRY.value
                if blocker
                in {
                    c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
                    c.BlockerClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value,
                }
                else c.FillRouteClass.FILL_FROM_OWNER_INPUT_RESPONSE.value
            ),
            "future_pr_route": future_route,
            "exact_steps_to_fill": list(record.get("codex_actionable_completion_steps") or []),
            "exact_acceptance_criteria": record.get("exact_unblock_condition"),
            "validator_that_will_unblock": (
                "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
            ),
        }
    ]


def build_pr154_records(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        population = source_population(record)
        complete = bool(record.get("materialization_allowed"))
        record_id = text(record.get("pr154_record_id"))
        blocker = _blocker_class(population, complete)
        future_route = _future_route(population, complete)
        editability = owner_editability.for_pr154_record(record, population)
        agent = agent_for_pr154_record(record, blocked=not complete)
        authority_profiles = (
            c.SOURCE_EVIDENCE_AUTHORITY_PROFILE_IDS
            if population
            in {
                c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
                c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
            }
            else c.OWNER_EDITABLE_AUTHORITY_PROFILE_IDS
            if editability["owner_dashboard_editable_flag"]
            else c.NONLIVE_AUTHORITY_PROFILE_IDS
        )
        owner_request_id = _owner_request_id(record_id, population, complete)
        output.append(
            {
                "target_id": record_id,
                "source_population": population,
                "public_external_subpopulation_or_null": (
                    "captured_candidates"
                    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value
                    else "pr153r_retry_candidates"
                    if population == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value
                    else None
                ),
                "prior_status": record.get("materialization_decision"),
                "completion_class": _completion_class(record, population),
                "materialization_state": (
                    c.MaterializationState.COMPLETE.value
                    if complete
                    else c.MaterializationState.PENDING_TYPED_FILL_PATH.value
                ),
                "value": record.get("materialized_value"),
                "value_type": record.get("materialized_value_type"),
                "unit_or_basis": record.get("materialized_value_unit"),
                "scale": record.get("materialized_value_scale"),
                "authority_class": pr154_authority_class(record, population),
                "authority_profile_ids": list(authority_profiles),
                "source_packet_ref_or_null": source_packet_ref(record),
                "quote_span_or_machine_field_locator_or_null": source_locator(record),
                "owner_input_request_id_or_null": owner_request_id,
                "owner_input_response_ref_or_null": None,
                "private_doc_attestation_ref_or_null": (
                    owner_request_id
                    if population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value
                    else None
                ),
                "split_reclassification_ref_or_null": (
                    owner_request_id
                    if population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value
                    else None
                ),
                "completion_evidence_ref": (
                    source_packet_ref(record) or "PR154_BLOCKED_COMPLETION_PATH"
                ),
                "downstream_pr155_ref_or_null": (
                    "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json"
                ),
                "downstream_pr156_binding_ref_or_null": (
                    "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.registry.json"
                ),
                "downstream_scoring_ranking_future_eligibility": [
                    c.FutureEligibility.ELIGIBLE_FOR_SCORING_RANKING_BRIDGE_PR164.value
                ]
                if complete
                else [c.FutureEligibility.NOT_ELIGIBLE_BLOCKED.value],
                "atomicrows_mapping_ref_or_null": None,
                "blocker_class": blocker,
                "remaining_blockers": [] if complete else [blocker],
                "fill_plan_refs": _fill_plan_ref(record, blocker, future_route),
                "exact_next_action_if_not_complete": None
                if complete
                else record.get("required_next_task"),
                "future_pr_route": future_route,
                "quantum_classical_compatibility": [
                    c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value
                ],
                **editability,
                **agent,
                "market_specific_launch_readiness_refs": [
                    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
                ],
                "orchestration_refs": [
                    "docs/master_plan/generated/PR136RouteTriage.report.json",
                    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
                ],
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(output, key=lambda item: item["target_id"])


def count_invariant_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    lanes = Counter(source_population(record) for record in records)
    base_counts = dict(c.PR154_BASE_PARTITION_COUNTS)
    sub_counts = dict(c.PR154_PUBLIC_EXTERNAL_SUBPARTITION_COUNTS)
    actual_base_counts = {
        "public_external_denominator_targets": lanes[
            c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value
        ]
        + lanes[c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value],
        "internal_control_plane_targets": lanes[
            c.SourcePopulation.PR154_INTERNAL_CONTROL_PLANE.value
        ],
        "split_reclassification_targets": lanes[
            c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value
        ],
        "private_doc_attestation_targets": lanes[
            c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value
        ],
        "owner_route_targets": lanes[c.SourcePopulation.PR154_OWNER_ROUTE.value],
    }
    actual_sub_counts = {
        "captured_candidates": lanes[c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value],
        "pr153r_retry_candidates": lanes[c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value],
    }
    base_sum = sum(actual_base_counts.values())
    sub_sum = sum(actual_sub_counts.values())
    return {
        "total_pr154_targets": len(records),
        "base_partition_counts": actual_base_counts,
        "expected_base_partition_counts": base_counts,
        "public_external_subpartition_counts": actual_sub_counts,
        "expected_public_external_subpartition_counts": sub_counts,
        "base_partition_sum": base_sum,
        "public_external_subpartition_sum": sub_sum,
        "atomicrows_universe_count": c.EXPECTED_ATOMICROWS_TOTAL,
        "count_invariants_passed_flag": (
            len(records) == c.EXPECTED_PR154_TOTAL
            and actual_base_counts == base_counts
            and actual_sub_counts == sub_counts
            and base_sum == c.EXPECTED_PR154_TOTAL
            and sub_sum == base_counts["public_external_denominator_targets"]
        ),
        "any_missing_input_count_source": False,
    }


def aggregate_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [
        record for record in records if record["materialization_state"] == c.MaterializationState.COMPLETE.value
    ]
    blocked = [record for record in records if record not in completed]
    return {
        "total_pr154_targets": len(records),
        "completed_count": len(completed),
        "completed_from_existing_evidence_count": sum(
            1
            for record in completed
            if record["source_population"] == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value
        ),
        "owner_input_required_count": sum(
            1 for record in records if record["blocker_class"] == c.BlockerClass.OWNER_INPUT_REQUIRED.value
        ),
        "private_doc_attestation_required_count": sum(
            1
            for record in records
            if record["blocker_class"] == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
        ),
        "split_reclassification_required_count": sum(
            1
            for record in records
            if record["blocker_class"] == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value
        ),
        "public_source_retry_still_required_count": sum(
            1
            for record in records
            if record["blocker_class"] == c.BlockerClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value
        ),
        "schema_invalid_count": sum(
            1 for record in records if record["blocker_class"] == c.BlockerClass.SCHEMA_INVALID.value
        ),
        "ambiguous_blocked_count": sum(
            1 for record in records if record["completion_class"] == c.CompletionClass.BLOCKED_AMBIGUOUS.value
        ),
        "authority_missing_count": sum(
            1 for record in records if record["authority_class"] == c.AuthorityClass.MISSING_OWNER_INPUT.value
        ),
        "future_pr_routing_counts": stable_counter_from_records(records, "future_pr_route"),
        "owner_editability_counts": stable_counter_from_records(records, "owner_editability_class"),
        "agent_binding_state_counts": stable_counter_from_records(records, "agent_binding_state"),
        "no_orphan_status_counts": stable_counter_from_records(records, "no_orphan_status"),
        "all_no_authority_counts": dict(c.ZERO_NO_AUTHORITY_COUNTS),
        "blocked_count": len(blocked),
    }
