"""AtomicRows 4183 completion/materialization registry."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from . import owner_editability
from .agent_responsibility_bridge import for_atomicrow as agent_for_atomicrow
from .atomicrows_fill_path import build_fill_plan
from .atomicrows_source_requirement_classification import (
    classify_primary,
    compatibility_for_row,
    secondary_tags,
)
from .io import stable_counter, stable_counter_from_records, text


COMPLETED_PRIMARY_CLASSES = {
    c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE.value,
    c.AtomicRowsSourceRequirementClass.EXISTING_ACCEPTED_OR_MATERIALIZED_VALUE.value,
    c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value,
    c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED.value,
    c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value,
}


def _authority_class(primary: str) -> str:
    if primary == c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE.value:
        return c.AuthorityClass.OWNER_INTERNAL_POLICY.value
    if primary == c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value:
        return c.AuthorityClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value
    if primary == c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED.value:
        return c.AuthorityClass.FORMULA_ONLY_CANONICAL_INTERNAL.value
    if primary == c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value:
        return c.AuthorityClass.NON_AUTHORITY_METADATA_ONLY.value
    if primary in {
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED.value,
    }:
        return c.AuthorityClass.MISSING_EXTERNAL_SOURCE_EVIDENCE.value
    if primary == c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value:
        return c.AuthorityClass.MISSING_AGENT_BINDING.value
    return c.AuthorityClass.MISSING_OWNER_INPUT.value


def _completion_class(primary: str, complete: bool) -> str:
    if complete:
        if primary == c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE.value:
            return c.CompletionClass.ATOMICROWS_FIELD_FILLED_FROM_INTERNAL_POLICY.value
        if primary == c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value:
            return c.CompletionClass.ATOMICROWS_FIELD_DERIVED_FROM_ACCEPTED_INPUTS.value
        if primary == c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED.value:
            return c.CompletionClass.ATOMICROWS_FIELD_FILLED_FROM_CANONICAL_FORMULA.value
        return c.CompletionClass.ATOMICROWS_ROW_COMPLETION_CLASSIFIED.value
    return c.CompletionClass.ATOMICROWS_FIELD_BLOCKED_WITH_FILL_PLAN.value


def _blocker_class(primary: str, complete: bool) -> str:
    if complete:
        return c.BlockerClass.NONE.value
    if primary in {
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED.value,
    }:
        return c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value
    if primary == c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value:
        return c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value
    if primary == c.AtomicRowsSourceRequirementClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value:
        return c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
    if primary == c.AtomicRowsSourceRequirementClass.SPLIT_RECLASSIFICATION_REQUIRED.value:
        return c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value
    if primary == c.AtomicRowsSourceRequirementClass.UNKNOWN_REQUIRES_TRIAGE.value:
        return c.BlockerClass.AMBIGUOUS_ROUTE.value
    return c.BlockerClass.OWNER_INPUT_REQUIRED.value


def _future_eligibility(primary: str, complete: bool, blocker: str) -> list[str]:
    if not complete:
        if blocker == c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value:
            return [c.FutureEligibility.ELIGIBLE_FOR_PUBLIC_RETRY_PR159.value]
        if blocker == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value:
            return [c.FutureEligibility.ELIGIBLE_FOR_AGENT_BINDING_PR163.value]
        if blocker == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value:
            return [c.FutureEligibility.ELIGIBLE_FOR_SPLIT_RECLASSIFICATION_PR160.value]
        return [c.FutureEligibility.ELIGIBLE_FOR_OWNER_INPUT_PR158.value]
    if primary == c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value:
        return [
            c.FutureEligibility.ELIGIBLE_FOR_SCORING_RANKING_BRIDGE_PR164.value,
            c.FutureEligibility.ELIGIBLE_FOR_OPTIMIZER_INTERFACE_PR167.value,
            c.FutureEligibility.ELIGIBLE_FOR_QUANTUM_BACKEND_GATED_SANDBOX_PR169.value,
        ]
    return [
        c.FutureEligibility.ELIGIBLE_FOR_SCORING_RANKING_BRIDGE_PR164.value,
        c.FutureEligibility.ELIGIBLE_FOR_REPLAY_AFTER_FUTURE_GATES.value,
        c.FutureEligibility.ELIGIBLE_FOR_PAPER_AFTER_FUTURE_GATES.value,
    ]


def _owner_request_id(row_id: str, blocker: str) -> str | None:
    if blocker == c.BlockerClass.OWNER_INPUT_REQUIRED.value:
        return f"PR157_ATOMICROWS_OWNER_INPUT_REQUEST__{row_id}"
    if blocker == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value:
        return f"PR157_ATOMICROWS_AGENT_ASSIGNMENT_REQUEST__{row_id}"
    if blocker == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value:
        return f"PR157_ATOMICROWS_PRIVATE_DOC_REQUEST__{row_id}"
    if blocker == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value:
        return f"PR157_ATOMICROWS_SPLIT_RECLASSIFICATION_REQUEST__{row_id}"
    return None


def _missing_field(blocker: str) -> str:
    if blocker == c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value:
        return "accepted_source_evidence_packet"
    if blocker == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value:
        return "exact_agent_binding_or_owner_assignment"
    if blocker == c.BlockerClass.OWNER_INPUT_REQUIRED.value:
        return "owner_internal_policy_value"
    if blocker == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value:
        return "private_doc_attestation"
    if blocker == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value:
        return "split_reclassification_basis"
    return "triage_basis"


def build_atomicrow_records(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        row_id = text(row.get("row_id"))
        family_id = text(row.get("family_id") or row.get("source_file_family_id"))
        primary = classify_primary(row)
        complete = primary in COMPLETED_PRIMARY_CLASSES
        blocker = _blocker_class(primary, complete)
        owner_request_id = _owner_request_id(row_id, blocker)
        fill_plans: list[dict[str, Any]] = []
        if blocker != c.BlockerClass.NONE.value:
            fill_plans.append(
                build_fill_plan(
                    row_id=row_id,
                    missing_field_id=_missing_field(blocker),
                    blocker_class=blocker,
                    owner_question_id=owner_request_id
                    if blocker
                    in {
                        c.BlockerClass.OWNER_INPUT_REQUIRED.value,
                        c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value,
                    }
                    else None,
                    source_target_id=row_id
                    if blocker == c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value
                    else None,
                    private_doc_attestation_request_id=owner_request_id
                    if blocker == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
                    else None,
                    split_reclassification_request_id=owner_request_id
                    if blocker == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value
                    else None,
                )
            )
        editability = owner_editability.for_atomicrow(primary, family_id)
        agent = agent_for_atomicrow(
            row,
            source_requirement_class=primary,
            owner_assignment_request_id=owner_request_id
            if blocker == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value
            else None,
        )
        future = _future_eligibility(primary, complete, blocker)
        compatibility = compatibility_for_row(row, primary)
        records.append(
            {
                "row_id_or_row_ref": row_id,
                "shard_id_if_applicable": None,
                "family_id": family_id,
                "parameter_id": row_id,
                "formula_algorithm_edge_alpha_id_or_null": None,
                "source_requirement_class": primary,
                "secondary_tags": secondary_tags(row, primary),
                "value_materialization_status": (
                    "MATERIALIZED_FROM_EXISTING_EXACT_ROW_SOURCE"
                    if complete
                    else "BLOCKED_WITH_TYPED_FILL_PLAN"
                ),
                "completion_class": _completion_class(primary, complete),
                "authority_class": _authority_class(primary),
                "authority_profile_ids": list(
                    c.OWNER_EDITABLE_AUTHORITY_PROFILE_IDS
                    if editability["owner_dashboard_editable_flag"]
                    else c.SOURCE_EVIDENCE_AUTHORITY_PROFILE_IDS
                    if editability["factual_external_value_flag"]
                    else c.NONLIVE_AUTHORITY_PROFILE_IDS
                ),
                "owner_input_required_flag": blocker
                in {
                    c.BlockerClass.OWNER_INPUT_REQUIRED.value,
                    c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value,
                },
                "public_source_required_flag": blocker
                == c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
                "private_doc_required_flag": blocker
                == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value,
                "internal_policy_default_flag": primary
                == c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE.value,
                "agent_binding_candidate_flag": primary
                == c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value,
                "scoring_ranking_candidate_flag": True,
                "optimizer_future_candidate_flag": any(
                    item
                    in {
                        c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value,
                        c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value,
                        c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
                    }
                    for item in compatibility
                ),
                "replay_paper_future_candidate_flag": True,
                "classical_quantum_applicability_ref": row.get("quantum_metadata"),
                "quantum_classical_compatibility": compatibility,
                "AtomicRows_semantic_contract_ref": (
                    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
                ),
                "AtomicRows_reconciliation_ref": (
                    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
                ),
                "completion_evidence_ref": text(row.get("_source_jsonl_path")),
                "blocker_class": blocker,
                "remaining_blockers": [] if complete else [blocker],
                "fill_plan_refs": [plan["fill_plan_id"] for plan in fill_plans],
                "unresolved_field_fill_plans": fill_plans,
                "future_scoring_ranking_eligibility": future,
                "future_optimizer_eligibility": [
                    c.FutureEligibility.ELIGIBLE_FOR_OPTIMIZER_INTERFACE_PR167.value
                ],
                "future_replay_paper_eligibility": [
                    c.FutureEligibility.ELIGIBLE_FOR_REPLAY_AFTER_FUTURE_GATES.value,
                    c.FutureEligibility.ELIGIBLE_FOR_PAPER_AFTER_FUTURE_GATES.value,
                ],
                "future_live_eligibility": [
                    c.FutureEligibility.ELIGIBLE_FOR_LIVE_ONLY_AFTER_ALL_FUTURE_GATES.value
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
    return sorted(records, key=lambda item: item["row_id_or_row_ref"])


def source_requirement_count_fields(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = stable_counter(str(record["source_requirement_class"]) for record in records)
    return {
        "atomicrows_total_count": len(records),
        "internal_control_plane_count": counts.get(
            c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE.value, 0
        ),
        "owner_route_count": counts.get(c.AtomicRowsSourceRequirementClass.OWNER_ROUTE.value, 0),
        "owner_policy_default_count": counts.get(
            c.AtomicRowsSourceRequirementClass.OWNER_POLICY_DEFAULT.value, 0
        ),
        "private_doc_attestation_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value, 0
        ),
        "public_external_source_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value, 0
        ),
        "public_external_already_captured_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_ALREADY_CAPTURED.value, 0
        ),
        "public_external_retry_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value, 0
        ),
        "split_reclassification_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.SPLIT_RECLASSIFICATION_REQUIRED.value, 0
        ),
        "existing_accepted_or_materialized_value_count": counts.get(
            c.AtomicRowsSourceRequirementClass.EXISTING_ACCEPTED_OR_MATERIALIZED_VALUE.value,
            0,
        ),
        "generated_derivative_from_accepted_inputs_count": counts.get(
            c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value,
            0,
        ),
        "formula_only_no_external_value_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED.value, 0
        ),
        "parameter_range_owner_policy_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_OWNER_POLICY.value, 0
        ),
        "parameter_range_source_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED.value, 0
        ),
        "agent_binding_required_count": counts.get(
            c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value, 0
        ),
        "quantum_classical_metadata_only_count": counts.get(
            c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value, 0
        ),
        "unknown_requires_triage_count": counts.get(
            c.AtomicRowsSourceRequirementClass.UNKNOWN_REQUIRES_TRIAGE.value, 0
        ),
    }


def aggregate_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [
        record
        for record in records
        if record["blocker_class"] == c.BlockerClass.NONE.value
    ]
    fill_plan_count = sum(len(record["unresolved_field_fill_plans"]) for record in records)
    unresolved_field_count = fill_plan_count
    count_fields = source_requirement_count_fields(records)
    secondary_tags_flat = [
        tag for record in records for tag in record.get("secondary_tags", [])
    ]
    future_eligibility_flat = [
        item
        for record in records
        for key in (
            "future_scoring_ranking_eligibility",
            "future_optimizer_eligibility",
            "future_replay_paper_eligibility",
            "future_live_eligibility",
        )
        for item in record.get(key, [])
    ]
    compatibility_flat = [
        item for record in records for item in record.get("quantum_classical_compatibility", [])
    ]
    authority_profile_flat = [
        item for record in records for item in record.get("authority_profile_ids", [])
    ]
    source_count_sum = sum(
        value
        for key, value in count_fields.items()
        if key.endswith("_count") and key != "atomicrows_total_count"
    )
    return {
        "atomicrows_total_universe_count": len(records),
        "processed_count": len(records),
        "sharded_count": len(records),
        "completed_count": len(completed),
        "pending_count": len(records) - len(completed),
        "not_materializable_current_inputs_count": len(records) - len(completed),
        "owner_input_required_count": sum(
            1 for record in records if record["owner_input_required_flag"]
        ),
        "public_source_required_count": sum(
            1 for record in records if record["public_source_required_flag"]
        ),
        "private_doc_required_count": sum(
            1 for record in records if record["private_doc_required_flag"]
        ),
        "internal_policy_default_count": sum(
            1 for record in records if record["internal_policy_default_flag"]
        ),
        "classification_count_by_source_requirement_class": stable_counter_from_records(
            records,
            "source_requirement_class",
        ),
        "secondary_tag_counts": stable_counter(secondary_tags_flat),
        "fill_plan_count": fill_plan_count,
        "placeholder_value_count": 0,
        "unresolved_field_count": unresolved_field_count,
        "owner_editability_class_counts": stable_counter_from_records(
            records,
            "owner_editability_class",
        ),
        "owner_dashboard_editable_count": sum(
            1 for record in records if record["owner_dashboard_editable_flag"]
        ),
        "owner_change_requires_replay_count": sum(
            1 for record in records if record["owner_change_requires_replay_flag"]
        ),
        "owner_change_requires_paper_count": sum(
            1 for record in records if record["owner_change_requires_paper_flag"]
        ),
        "owner_change_blocks_live_until_review_count": sum(
            1 for record in records if record["owner_change_blocks_live_until_review_flag"]
        ),
        "no_orphan_status_counts": stable_counter_from_records(records, "no_orphan_status"),
        "agent_binding_state_counts": stable_counter_from_records(records, "agent_binding_state"),
        "orphan_count": sum(
            1
            for record in records
            if record["no_orphan_status"]
            == c.NoOrphanStatus.ORPHAN_BLOCKED_NO_RESPONSIBLE_ROUTE.value
        ),
        "classical_compatibility_count": sum(
            1
            for item in compatibility_flat
            if item
            in {
                c.QuantumClassicalCompatibility.CLASSICAL_FORMULA_COMPATIBLE.value,
                c.QuantumClassicalCompatibility.CLASSICAL_TRADING_ALGORITHM_COMPATIBLE.value,
                c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value,
            }
        ),
        "quantum_inspired_candidate_count": compatibility_flat.count(
            c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value
        ),
        "true_quantum_candidate_count": compatibility_flat.count(
            c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value
        ),
        "hybrid_candidate_count": compatibility_flat.count(
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value
        ),
        "classical_only_baseline_count": compatibility_flat.count(
            c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value
        ),
        "unknown_compatibility_blocked_count": compatibility_flat.count(
            c.QuantumClassicalCompatibility.UNKNOWN_COMPATIBILITY_BLOCKED.value
        ),
        "source_requirement_class_counts": count_fields,
        "source_requirement_class_sum": source_count_sum,
        "future_eligibility_counts": stable_counter(future_eligibility_flat),
        "authority_profile_counts": stable_counter(authority_profile_flat),
        "count_reconciliation_passed_flag": (
            len(records) == c.EXPECTED_ATOMICROWS_TOTAL
            and source_count_sum == c.EXPECTED_ATOMICROWS_TOTAL
        ),
    }
