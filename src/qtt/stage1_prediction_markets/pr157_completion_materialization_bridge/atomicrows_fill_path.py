"""Typed fill-path builders for unresolved PR157 fields."""

from __future__ import annotations

from typing import Any

from . import constants as c


def route_for_blocker(blocker: str) -> tuple[str, str, str, list[str]]:
    if blocker == c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value:
        return (
            c.FillRouteClass.FILL_AFTER_PUBLIC_SOURCE_RETRY.value,
            c.RequiredActor.FUTURE_SOURCE_EVIDENCE_TOOLING.value,
            "ACCEPTED_TARGET_FIELD_SOURCE_EVIDENCE_PACKET",
            ["ELIGIBLE_FOR_PUBLIC_RETRY_PR159"],
        )
    if blocker == c.BlockerClass.OWNER_INPUT_REQUIRED.value:
        return (
            c.FillRouteClass.FILL_FROM_OWNER_INPUT_RESPONSE.value,
            c.RequiredActor.OWNER.value,
            c.OWNER_RESPONSE_PATH.as_posix(),
            ["ELIGIBLE_FOR_OWNER_INPUT_PR158"],
        )
    if blocker == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value:
        return (
            c.FillRouteClass.FILL_AFTER_PRIVATE_DOC_ATTESTATION.value,
            c.RequiredActor.FUTURE_PRIVATE_DOC_ATTESTATION_WORKFLOW.value,
            "OWNER_PRIVATE_DOC_ATTESTATION_PACKET",
            ["ELIGIBLE_FOR_OWNER_INPUT_PR158"],
        )
    if blocker == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value:
        return (
            c.FillRouteClass.FILL_AFTER_SPLIT_RECLASSIFICATION.value,
            c.RequiredActor.FUTURE_RECLASSIFICATION_WORKFLOW.value,
            "TARGET_SPLIT_RECLASSIFICATION_PACKET",
            ["ELIGIBLE_FOR_SPLIT_RECLASSIFICATION_PR160"],
        )
    if blocker == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value:
        return (
            c.FillRouteClass.FILL_AFTER_AGENT_BINDING_MAP.value,
            c.RequiredActor.OWNER_AND_CODEX.value,
            "OWNER_AGENT_ASSIGNMENT_OR_EXACT_AGENT_BINDING_MAP",
            ["ELIGIBLE_FOR_AGENT_BINDING_PR163"],
        )
    return (
        c.FillRouteClass.FILL_BLOCKED_REQUIRES_TRIAGE.value,
        c.RequiredActor.OWNER_AND_CODEX.value,
        "TRIAGE_PACKET",
        ["ELIGIBLE_FOR_ATOMICROWS_SHARD_COMPLETION_PR161"],
    )


def build_fill_plan(
    *,
    row_id: str,
    missing_field_id: str,
    blocker_class: str,
    owner_question_id: str | None = None,
    source_target_id: str | None = None,
    private_doc_attestation_request_id: str | None = None,
    split_reclassification_request_id: str | None = None,
) -> dict[str, Any]:
    fill_route, actor, artifact, downstream = route_for_blocker(blocker_class)
    fill_plan_id = f"PR157_FILL_PLAN__{row_id}__{missing_field_id}"
    return {
        "row_id": row_id,
        "missing_field_id": missing_field_id,
        "blocker_class": blocker_class,
        "blocker_reason_code": blocker_class,
        "authority_gap_type": blocker_class,
        "fill_plan_id": fill_plan_id,
        "fill_route_class": fill_route,
        "required_actor": actor,
        "required_input_artifact": artifact,
        "exact_steps_to_fill": [
            f"Provide or consume {artifact} for {row_id}.",
            "Validate the artifact against PR157 authority and owner-editability rules.",
            "Regenerate PR157 outputs with the same deterministic sort order.",
        ],
        "exact_acceptance_criteria": (
            "The required field is non-null, target-scoped, authority-compatible, "
            "and the PR157 validator reports no blocker for this fill plan."
        ),
        "validator_that_will_unblock": (
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "future_pr_route": downstream[0],
        "owner_question_id_or_null": owner_question_id,
        "source_target_id_or_null": source_target_id,
        "private_doc_attestation_request_id_or_null": private_doc_attestation_request_id,
        "split_reclassification_request_id_or_null": split_reclassification_request_id,
        "downstream_dependency_ids": downstream,
        "risk_if_unfilled": (
            "Row remains non-consumable for runtime/live use and cannot advance beyond "
            "metadata-only planning."
        ),
        "can_qtt_trade_without_this_row_flag": False,
        "can_qtt_use_row_in_replay_flag": False,
        "can_qtt_use_row_in_paper_flag": False,
        "can_qtt_use_row_in_live_flag": False,
    }
