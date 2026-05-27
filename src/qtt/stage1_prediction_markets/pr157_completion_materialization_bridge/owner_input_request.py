"""Owner input request packet construction."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _request_from_pr154(record: Mapping[str, Any]) -> dict[str, Any] | None:
    request_id = record.get("owner_input_request_id_or_null")
    if not request_id:
        return None
    blocker = str(record["blocker_class"])
    return {
        "request_id": request_id,
        "record_id_or_row_id": record["target_id"],
        "target_field_id_or_missing_field_id": record["target_id"],
        "source_population": record["source_population"],
        "atomicrows_source_requirement_class_or_null": None,
        "current_blocker_class": blocker,
        "exact_owner_question": (
            "Provide the exact owner-authorized packet required to unblock this "
            f"PR154 target without creating external-fact or live authority: {record['target_id']}"
        ),
        "requested_value_name": "pr154_completion_packet",
        "requested_value_type": record.get("owner_value_type"),
        "requested_unit_or_basis": record.get("owner_value_unit_or_basis"),
        "requested_scale": record.get("owner_value_scale"),
        "requested_platform_scope": None,
        "requested_market_scope": None,
        "internal_policy_or_external_fact_classification": (
            "OWNER_INTERNAL_OR_ATTESTATION_PACKET_NOT_EXTERNAL_FACT"
        ),
        "owner_may_answer_flag": True,
        "owner_answer_cannot_create_external_fact_flag": True,
        "owner_dashboard_future_control_ref_if_applicable": record.get(
            "future_dashboard_control_ref"
        ),
        "owner_editability_class_if_applicable": record.get("owner_editability_class"),
        "private_document_access_authorization_required_flag": blocker
        == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value,
        "private_document_identifier_if_applicable": None,
        "requested_private_doc_attestation_text_if_applicable": (
            "Owner attests that QTT may use the private document locator for this target."
            if blocker == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
            else None
        ),
        "agent_assignment_required_flag": False,
        "candidate_agent_roles_or_families_if_applicable": record.get(
            "candidate_agent_family_ids"
        ),
        "source_quote_or_machine_field_locator_required_if_external_fact": blocker
        in {
            c.BlockerClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
            c.BlockerClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value,
        },
        "exact_unblock_condition": record.get("exact_next_action_if_not_complete")
        or "OWNER_RESPONSE_ACCEPTED",
        "exact_steps_to_fill": [
            "Complete the owner response item for this request_id.",
            "Confirm no external fact, runtime, live, order, fill, or profit authority is created.",
            "Rerun the PR157 validator with the response file present.",
        ],
        "exact_acceptance_criteria": (
            "Response item has a supported authority class, non-ambiguous value or explicit "
            "decline, and all attestation fields required by the blocker."
        ),
        "validator_that_will_unblock": (
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "risk_of_leaving_blocked": "Target remains blocked from downstream consumption.",
        "downstream_prs_blocked": [record.get("future_pr_route")],
        "default_if_unanswered": None,
        "validation_rule_ids": [
            "PR157_OWNER_RESPONSE_SCHEMA",
            "PR157_NO_EXTERNAL_FACT_FABRICATION",
            "PR157_NO_RUNTIME_LIVE_ORDER_AUTHORITY",
        ],
        "authority_profile_ids": record.get("authority_profile_ids"),
    }


def _request_from_atomicrow(record: Mapping[str, Any]) -> dict[str, Any] | None:
    request_id = record.get("owner_agent_assignment_request_id_or_null")
    if not request_id:
        for plan in record.get("unresolved_field_fill_plans", []):
            request_id = plan.get("owner_question_id_or_null")
            if request_id:
                break
    if not request_id:
        return None
    blocker = str(record["blocker_class"])
    missing_field = None
    if record.get("unresolved_field_fill_plans"):
        missing_field = record["unresolved_field_fill_plans"][0].get("missing_field_id")
    return {
        "request_id": request_id,
        "record_id_or_row_id": record["row_id_or_row_ref"],
        "target_field_id_or_missing_field_id": missing_field,
        "source_population": c.SourcePopulation.ATOMICROWS_4183_UNIVERSE.value,
        "atomicrows_source_requirement_class_or_null": record["source_requirement_class"],
        "current_blocker_class": blocker,
        "exact_owner_question": (
            "Provide the exact owner-controlled value or assignment needed for "
            f"{record['row_id_or_row_ref']} without creating external-fact or live authority."
        ),
        "requested_value_name": missing_field,
        "requested_value_type": record.get("owner_value_type"),
        "requested_unit_or_basis": record.get("owner_value_unit_or_basis"),
        "requested_scale": record.get("owner_value_scale"),
        "requested_platform_scope": "PREDICTION_MARKETS_GENERAL",
        "requested_market_scope": "PREDICTION_MARKETS_GENERAL",
        "internal_policy_or_external_fact_classification": (
            "OWNER_INTERNAL_POLICY_OR_AGENT_ASSIGNMENT_NOT_EXTERNAL_FACT"
        ),
        "owner_may_answer_flag": True,
        "owner_answer_cannot_create_external_fact_flag": True,
        "owner_dashboard_future_control_ref_if_applicable": record.get(
            "future_dashboard_control_ref"
        ),
        "owner_editability_class_if_applicable": record.get("owner_editability_class"),
        "private_document_access_authorization_required_flag": blocker
        == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value,
        "private_document_identifier_if_applicable": None,
        "requested_private_doc_attestation_text_if_applicable": None,
        "agent_assignment_required_flag": blocker
        == c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value,
        "candidate_agent_roles_or_families_if_applicable": record.get(
            "candidate_agent_family_ids"
        ),
        "source_quote_or_machine_field_locator_required_if_external_fact": False,
        "exact_unblock_condition": (
            record["unresolved_field_fill_plans"][0]["exact_acceptance_criteria"]
            if record.get("unresolved_field_fill_plans")
            else "OWNER_RESPONSE_ACCEPTED"
        ),
        "exact_steps_to_fill": (
            record["unresolved_field_fill_plans"][0]["exact_steps_to_fill"]
            if record.get("unresolved_field_fill_plans")
            else []
        ),
        "exact_acceptance_criteria": (
            record["unresolved_field_fill_plans"][0]["exact_acceptance_criteria"]
            if record.get("unresolved_field_fill_plans")
            else "OWNER_RESPONSE_ACCEPTED"
        ),
        "validator_that_will_unblock": (
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "risk_of_leaving_blocked": "AtomicRows row remains non-consumable for runtime/live use.",
        "downstream_prs_blocked": record.get("future_scoring_ranking_eligibility"),
        "default_if_unanswered": None,
        "validation_rule_ids": [
            "PR157_OWNER_RESPONSE_SCHEMA",
            "PR157_NO_EXTERNAL_FACT_FABRICATION",
            "PR157_NO_RUNTIME_LIVE_ORDER_AUTHORITY",
        ],
        "authority_profile_ids": record.get("authority_profile_ids"),
    }


def build_owner_request_packet(
    pr154_records: list[Mapping[str, Any]],
    atomicrow_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    requests = [
        request
        for request in (
            [_request_from_pr154(record) for record in pr154_records]
            + [_request_from_atomicrow(record) for record in atomicrow_records]
        )
        if request is not None
    ]
    requests = sorted(requests, key=lambda item: str(item["request_id"]))
    return {
        "packet_id": "PR157_OWNER_COMPLETION_INPUT_REQUEST_PACKET",
        "schema_version": "pr157.owner_completion_input_request.v1",
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "owner_response_path": c.OWNER_RESPONSE_PATH.as_posix(),
        "do_not_create_response_file_without_owner_input": True,
        "request_count": len(requests),
        "response_validator": (
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "requests": requests,
        "authority_profile_ids": list(c.OWNER_EDITABLE_AUTHORITY_PROFILE_IDS),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }
