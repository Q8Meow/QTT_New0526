"""Owner-editability lifecycle classification for PR157."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _editable_payload(
    editability: c.OwnerEditabilityClass,
    *,
    editable: bool,
    scope: str,
    value_type: str = "INTERNAL_POLICY_METADATA",
    unit_or_basis: str = "NOT_APPLICABLE",
    scale: str = "NOT_APPLICABLE",
    allowed_range_or_enum: Any = None,
    factual_external: bool = False,
) -> dict[str, Any]:
    requires_retest = editable
    return {
        "owner_editability_class": editability.value,
        "owner_dashboard_editable_flag": editable,
        "owner_value_change_allowed_flag": editable,
        "owner_value_change_scope": scope,
        "owner_value_type": value_type,
        "allowed_owner_value_range_or_enum": allowed_range_or_enum,
        "owner_value_unit_or_basis": unit_or_basis,
        "owner_value_scale": scale,
        "factual_external_value_flag": factual_external,
        "external_fact_override_forbidden_flag": factual_external or not editable,
        "owner_policy_assumption_allowed_for_replay_paper_flag": editable,
        "owner_policy_assumption_live_blocked_until_gates_flag": editable,
        "owner_change_requires_policy_snapshot_flag": editable,
        "owner_change_requires_replay_flag": requires_retest,
        "owner_change_requires_paper_flag": requires_retest,
        "owner_change_allows_shadow_after_gates_flag": editable,
        "owner_change_requires_dual_result_review_flag": editable,
        "owner_change_requires_owner_promotion_review_flag": editable,
        "owner_change_blocks_live_until_review_flag": editable,
        "open_orders_unchanged_by_value_change_flag": True,
        "open_positions_unchanged_by_value_change_flag": True,
        "exact_retest_route": (
            "FUTURE_POLICY_SNAPSHOT_THEN_REPLAY_PAPER_DUAL_REVIEW"
            if editable
            else "NOT_OWNER_EDITABLE_SOURCE_OR_RUNTIME_FACT"
        ),
        "future_dashboard_control_ref": (
            f"PR157_DASHBOARD_CONTROL::{editability.value}::{scope}" if editable else None
        ),
        "future_replay_paper_route": (
            "FUTURE_REPLAY_PAPER_AFTER_POLICY_SNAPSHOT" if editable else None
        ),
        "future_shadow_route": "FUTURE_SHADOW_AFTER_LIVE_ADJACENT_GATES" if editable else None,
        "future_live_promotion_route": (
            "FUTURE_OWNER_PROMOTION_REVIEW_AFTER_ALL_LIVE_GATES" if editable else None
        ),
    }


def for_pr154_record(record: Mapping[str, Any], source_population: str) -> dict[str, Any]:
    if source_population in {
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
    }:
        return _editable_payload(
            c.OwnerEditabilityClass.SOURCE_FACT_NOT_OWNER_EDITABLE,
            editable=False,
            scope="PUBLIC_EXTERNAL_FACT",
            value_type="EXTERNAL_FACT",
            factual_external=True,
        )
    if source_population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
        return _editable_payload(
            c.OwnerEditabilityClass.PRIVATE_DOC_ATTESTATION_REQUIRED_BEFORE_OWNER_USE,
            editable=True,
            scope="PRIVATE_DOC_ATTESTATION_PACKET",
            value_type="PRIVATE_DOC_ATTESTATION_METADATA",
        )
    if source_population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
        return _editable_payload(
            c.OwnerEditabilityClass.UNKNOWN_OWNER_EDITABILITY_REQUIRES_TRIAGE,
            editable=True,
            scope="SPLIT_RECLASSIFICATION_DECISION",
            value_type="RECLASSIFICATION_DECISION",
        )
    if source_population == c.SourcePopulation.PR154_OWNER_ROUTE.value:
        payload = _editable_payload(
            c.OwnerEditabilityClass.OWNER_EDITABLE_INTERNAL_POLICY,
            editable=True,
            scope="OWNER_ROUTE_PACKET_METADATA_ONLY",
            value_type="OWNER_ROUTE_PACKET",
        )
        payload["external_fact_override_forbidden_flag"] = True
        return payload
    return _editable_payload(
        c.OwnerEditabilityClass.OWNER_EDITABLE_INTERNAL_POLICY,
        editable=True,
        scope=str(record.get("parameter_family_or_target_family") or "INTERNAL_CONTROL_PLANE"),
    )


def for_atomicrow(source_requirement_class: str, family_id: str) -> dict[str, Any]:
    if source_requirement_class in {
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_ALREADY_CAPTURED.value,
    }:
        return _editable_payload(
            c.OwnerEditabilityClass.SOURCE_FACT_NOT_OWNER_EDITABLE,
            editable=False,
            scope="ATOMICROWS_EXTERNAL_SOURCE_DEPENDENT_FIELD",
            value_type="EXTERNAL_FACT",
            factual_external=True,
        )
    if source_requirement_class == c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value:
        return _editable_payload(
            c.OwnerEditabilityClass.OWNER_EDITABLE_AGENT_PERMISSION,
            editable=True,
            scope=family_id,
            value_type="AGENT_ASSIGNMENT_OR_PERMISSION",
        )
    if source_requirement_class == c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value:
        return _editable_payload(
            c.OwnerEditabilityClass.OWNER_EDITABLE_QUANTUM_PRIORITY,
            editable=True,
            scope=family_id,
            value_type="QUANTUM_PRIORITY_METADATA",
        )
    if "risk" in family_id:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_RISK_LIMIT
    elif "capital" in family_id:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_CAPITAL_ALLOCATION
    elif "scoring" in family_id:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_SCORING_WEIGHT
    elif "replay_paper" in family_id:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_REPLAY_PAPER_ASSUMPTION
    elif "latency" in family_id or "error_guard" in family_id:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_FORMULA_THRESHOLD
    elif source_requirement_class == c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS.value:
        return _editable_payload(
            c.OwnerEditabilityClass.DERIVED_FROM_ACCEPTED_INPUTS_ONLY,
            editable=False,
            scope=family_id,
            value_type="DERIVED_VALUE",
        )
    else:
        editability = c.OwnerEditabilityClass.OWNER_EDITABLE_INTERNAL_POLICY
    return _editable_payload(editability, editable=True, scope=family_id)
