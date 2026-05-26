"""Small PR153 data-model helpers used by report generation and tests."""

from __future__ import annotations

from typing import Any, Mapping

from . import reason_codes as rc


OWNER_DECISION_OPTIONS = (
    "OWNER_OVERRIDE_BLOCKER",
    "OWNER_APPROVE_BLOCKER_OR_CANDIDATE_FOR_NEXT_REVIEW",
    "OWNER_PROVIDE_VALUE",
    "OWNER_DISAPPROVE",
)

OWNER_NON_SOURCE_BACKED_STATUSES = (
    "OWNER_AUTHORIZED_NON_SOURCE_BACKED_CANDIDATE",
    "OWNER_AUTHORIZED_NON_SOURCE_BACKED_RUNTIME_VALUE_PENDING_LATER_OWNER_COMMAND",
)

OWNER_DECISION_STATUS_BY_TYPE = {
    "OWNER_OVERRIDE_BLOCKER": "OWNER_OVERRIDE_RECORDED_PR154_WORKFLOW_GATE_BYPASSED",
    "OWNER_APPROVE_BLOCKER_OR_CANDIDATE_FOR_NEXT_REVIEW": "OWNER_APPROVED_FOR_PR154_REVIEW",
    "OWNER_PROVIDE_VALUE": "OWNER_PROVIDED_EXTERNAL_FACT_CANDIDATE_VALUE",
    "OWNER_DISAPPROVE": "OWNER_DISAPPROVED_TARGET_BLOCKED",
}

INTERNAL_POLICY_FIELD_IDS = {
    "candidate_count",
    "lane_separation",
    "no_automatic_live_promotion",
    "no_result_fabrication",
    "promotion_gate_input",
}

INTERNAL_ARCHITECTURE_FIELD_IDS = {
    "candidate_inventory_links",
    "future_agent_family_eligibility_dependencies",
    "future_source_materialization_dependencies",
    "no_bundle_mutation_state",
    "pr149_materialization_targets",
    "row_family_references",
    "semantic_field_references",
}


def no_claim_flags(source_capture_candidate_created: bool) -> dict[str, bool]:
    return {
        "source_capture_candidate_created": source_capture_candidate_created,
        "source_fact_acceptance_created": False,
        "accepted_source_evidence_packet_created": False,
        "accepted_default_value_created": False,
        "connector_semantic_value_created": False,
        "connector_binding_created": False,
        "runtime_cash_value_created": False,
        "runtime_cash_receipt_created": False,
        "order_parameter_created": False,
        "order_execution_created": False,
        "live_reachability_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_paper_result_created": False,
        "replay_paper_truth_input_created": False,
        "launch_readiness_input_created": False,
        "profit_proof_created": False,
        "latency_superiority_proof_created": False,
        "quantum_backend_call_created": False,
        "quantum_simulator_call_created": False,
        "quantum_optimizer_output_created": False,
        "quantum_superiority_proof_created": False,
        "quantum_advantage_evidence_created": False,
        "launch_readiness_created": False,
        "final_readiness_created": False,
        "atomicrows_bundle_mutated": False,
        "atomicrows_value_materialized": False,
        "qtt_integrity_authority_created": False,
        "official_value_accepted": False,
        "hidden_default_created": False,
    }


def owner_non_source_backed_override_flags() -> dict[str, Any]:
    return {
        "source_backed_fact_created": False,
        "accepted_source_evidence_packet_created": False,
        "official_value_accepted": False,
        "source_truth_status": "OWNER_AUTHORIZED_NON_SOURCE_BACKED",
        "owner_override_receipt_required": True,
        "owner_assumes_external_fact_risk": True,
        "downstream_consumer_warning_required": True,
        "connector_use_allowed_without_later_owner_command": False,
        "runtime_use_allowed_without_later_owner_command": False,
        "order_use_allowed_without_later_owner_command": False,
        "replay_paper_truth_use_allowed_without_later_owner_command": False,
        "launch_readiness_use_allowed_without_later_owner_command": False,
        "atomicrows_materialization_allowed_without_later_owner_command": False,
    }


def field_authority_class(target_field_id: str) -> str:
    if target_field_id in INTERNAL_POLICY_FIELD_IDS:
        return "INTERNAL_QTT_POLICY_FIELD"
    if target_field_id in INTERNAL_ARCHITECTURE_FIELD_IDS:
        return "INTERNAL_QTT_ARCHITECTURE_FIELD"
    return "EXTERNAL_FACT_FIELD"


def owner_decision_receipt(
    unresolved_target: Mapping[str, Any],
    owner_decision_type: str,
    *,
    owner_provided_value: Any | None = None,
    owner_provided_value_unit_or_scale: str | None = None,
) -> dict[str, Any]:
    if owner_decision_type not in OWNER_DECISION_OPTIONS:
        raise ValueError(f"unknown owner decision type: {owner_decision_type}")

    field_id = str(unresolved_target.get("target_field_id") or "")
    authority_class = field_authority_class(field_id)
    is_external = authority_class == "EXTERNAL_FACT_FIELD"
    status = OWNER_DECISION_STATUS_BY_TYPE[owner_decision_type]
    if owner_decision_type == "OWNER_PROVIDE_VALUE":
        if authority_class == "INTERNAL_QTT_POLICY_FIELD":
            status = "OWNER_PROVIDED_INTERNAL_POLICY_VALUE"
        elif authority_class == "INTERNAL_QTT_ARCHITECTURE_FIELD":
            status = "OWNER_PROVIDED_INTERNAL_ARCHITECTURE_VALUE"
        else:
            status = "OWNER_PROVIDED_EXTERNAL_FACT_CANDIDATE_VALUE"

    receipt = {
        "owner_decision_receipt_id": (
            "PR153_OWNER_DECISION_RECEIPT__"
            f"{unresolved_target.get('retrieval_target_id')}__{owner_decision_type}"
        ),
        "retrieval_target_id": unresolved_target.get("retrieval_target_id"),
        "pr151_target_ref": unresolved_target.get("pr151_target_ref"),
        "pr150_target_ref": unresolved_target.get("pr150_target_ref"),
        "target_field_path": unresolved_target.get("target_field_path"),
        "platform_scope": unresolved_target.get("platform_scope"),
        "market_scope": unresolved_target.get("market_scope"),
        "priority_class": unresolved_target.get("priority_class"),
        "blocker_primary_category": unresolved_target.get("blocker_primary_category"),
        "blocker_secondary_categories": list(
            unresolved_target.get("blocker_secondary_categories", [])
        ),
        "owner_decision_type": owner_decision_type,
        "owner_decision_status": status,
        "owner_decision_basis": "OWNER_DECISION_RECEIPT_RECORDED_NOT_SOURCE_FACT_AUTHORITY",
        "owner_provided_value_if_any": owner_provided_value,
        "owner_provided_value_unit_or_scale_if_any": owner_provided_value_unit_or_scale,
        "field_authority_class": authority_class,
        "is_internal_qtt_policy_field": authority_class == "INTERNAL_QTT_POLICY_FIELD",
        "is_internal_qtt_architecture_field": authority_class
        == "INTERNAL_QTT_ARCHITECTURE_FIELD",
        "is_external_fact_field": is_external,
        "source_backed_fact_created": False,
        "accepted_source_evidence_packet_created": False,
        "official_value_accepted": False,
        "connector_semantic_value_created": False,
        "runtime_cash_value_created": False,
        "order_parameter_created": False,
        "launch_readiness_input_created": False,
        "atomicrows_value_materialized": False,
        "pr154_acceptance_required_for_external_fact": is_external,
        "owner_override_status_options": list(OWNER_NON_SOURCE_BACKED_STATUSES),
        "owner_override_receipt_required": True,
        "owner_override_receipt_status": "OWNER_OVERRIDE_RECEIPT_REQUIRED",
        "next_required_action": unresolved_target.get("next_required_action"),
        "no_claim_flags": no_claim_flags(False),
    }
    receipt.update(owner_non_source_backed_override_flags())
    if owner_decision_type == "OWNER_OVERRIDE_BLOCKER" and is_external:
        receipt["owner_decision_status"] = (
            "OWNER_OVERRIDE_RECORDED_EXTERNAL_FACT_STILL_NON_SOURCE_BACKED"
        )
    return receipt


def owner_provided_external_fact_candidate(
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = {
        "retrieval_target_id": receipt.get("retrieval_target_id"),
        "target_field_path": receipt.get("target_field_path"),
        "owner_provided_value": receipt.get("owner_provided_value_if_any"),
        "owner_provided_unit_or_scale_if_any": receipt.get(
            "owner_provided_value_unit_or_scale_if_any"
        ),
        "owner_value_authority_class": "OWNER_PROVIDED_CANDIDATE_ONLY_NOT_SOURCE_BACKED",
        "pr154_acceptance_required": True,
        "official_source_evidence_required": True,
        "connector_use_allowed": False,
        "runtime_use_allowed": False,
        "order_use_allowed": False,
        "replay_paper_truth_use_allowed": False,
        "launch_readiness_use_allowed": False,
        "atomicrows_materialization_allowed": False,
        "reason_codes": [
            "PR153_OWNER_PROVIDED_EXTERNAL_FACT_CANDIDATE_RECORDED",
            "PR153_OWNER_VALUE_REQUIRES_PR154_ACCEPTANCE",
            "PR153_OWNER_VALUE_NOT_CONNECTOR_USABLE",
            "PR153_OWNER_VALUE_NOT_RUNTIME_USABLE",
            "PR153_OWNER_VALUE_NOT_ORDER_USABLE",
            "PR153_OWNER_VALUE_NOT_LAUNCH_READINESS_USABLE",
            rc.PR153_OWNER_AUTHORIZED_NON_SOURCE_BACKED_CANDIDATE_ALLOWED,
            rc.PR153_OWNER_OVERRIDE_RECEIPT_REQUIRED,
        ],
    }
    candidate.update(owner_non_source_backed_override_flags())
    return candidate
