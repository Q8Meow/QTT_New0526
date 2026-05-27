"""PR154 deterministic materialization logic."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.pr153s_source_value_capture_closure_classifier import (
    taxonomy as pr153s_tx,
)

from . import inputs
from . import taxonomy as tx


PR153_REPORT_PATH = (
    "docs/master_plan/generated/PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json"
)
PR153R_REPORT_PATH = (
    "docs/master_plan/generated/PR153R_RedoExternalSourceValueCaptureTargets.report.json"
)
PR153S_REPORT_PATH = (
    "docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json"
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _non_empty(value: Any) -> bool:
    return bool(_text(value).strip())


def record_sort_key(record: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _text(record.get("platform_scope")),
        _text(record.get("target_field_path")),
        _text(record.get("source_pr153s_target_id")),
        _text(record.get("pr154_record_id")),
    )


def _base_record(pr153s_record: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _text(pr153s_record.get("target_id"))
    return {
        "pr154_record_id": f"PR154_BRIDGE__{source_id}",
        "source_pr153s_target_id": source_id,
        "pr153s_canonical_identity_key": pr153s_record.get("canonical_identity_key"),
        "platform_scope": pr153s_record.get("platform_scope"),
        "market_scope_if_available": pr153s_record.get("market_scope_if_available"),
        "target_field_path": pr153s_record.get("target_field_path"),
        "parameter_family_or_target_family": pr153s_record.get(
            "parameter_family_or_target_family"
        ),
        "pr153s_closure_lane": pr153s_record.get("closure_lane"),
        "pr153s_materialization_route": pr153s_record.get(
            "materialization_readiness_route"
        ),
        "accepted_source_packet_present": bool(
            pr153s_record.get("accepted_source_packet_present")
        ),
        "owner_internal_policy_required": False,
        "owner_internal_policy_present": False,
        "split_reclassification_required": bool(
            pr153s_record.get("split_or_reclassification_member")
        ),
        "private_doc_attestation_required": bool(
            pr153s_record.get("private_doc_attestation_member")
        ),
        "owner_route_packet_required": bool(pr153s_record.get("owner_route_member")),
        "runtime_receipt_required": bool(
            pr153s_record.get("runtime_receipt_route_member")
            or pr153s_record.get("runtime_receipt_required_before_value")
        ),
        "replay_paper_review_required": bool(
            pr153s_record.get("replay_paper_route_member")
            or pr153s_record.get("replay_paper_required_before_value")
        ),
        "quantum_execution_evidence_required": bool(
            pr153s_record.get("quantum_evidence_route_member")
            or pr153s_record.get("quantum_execution_required_before_value")
        ),
        "atomicrows_bundle_mutation_created": False,
        "atomicrows_bundle_hash_authority_created": False,
        "live_pretrade_consumption_allowed": False,
        "runtime_live_order_authority_created": False,
        "profit_evidence_created": False,
    }


def _quantum_class(pr153s_record: Mapping[str, Any]) -> str:
    upstream = _text(pr153s_record.get("quantum_forward_compatibility_class"))
    if upstream in tx.QUANTUM_FORWARD_CLASSES:
        return upstream
    if upstream in {
        pr153s_tx.QUANTUM_FORWARD_NOT_APPLICABLE,
        pr153s_tx.QUANTUM_FORWARD_METADATA_ONLY,
        pr153s_tx.QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY,
        pr153s_tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED,
        pr153s_tx.QUANTUM_FORWARD_UNKNOWN_FAIL_CLOSED,
    }:
        return upstream
    return tx.QUANTUM_FORWARD_UNKNOWN_FAIL_CLOSED


def _quantum_route(quantum_class: str) -> str:
    if quantum_class == tx.QUANTUM_FORWARD_NOT_APPLICABLE:
        return tx.QUANTUM_OPTIMIZER_ROUTE_NOT_APPLICABLE
    if quantum_class == tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED:
        return tx.QUANTUM_OPTIMIZER_ROUTE_EXECUTION_EVIDENCE_REQUIRED
    return tx.QUANTUM_OPTIMIZER_ROUTE_METADATA_ONLY


def _materialized_common(
    record: dict[str, Any],
    *,
    acceptance_decision: str,
    materialization_decision: str,
    materialized_value: Any,
    materialized_value_type: str,
    materialized_value_unit: str,
    materialized_value_scale: str,
    materialized_value_source_class: str,
    materialized_value_authority_class: str,
    materialized_value_authority_ref: str,
    materialized_value_source_path: str,
    materialized_value_source_record_key: str,
    materialized_value_source_field_path: str,
    official_source_locator: Any = None,
    quote_span_or_machine_field_locator: Any = None,
    candidate_value_present_upstream: bool = False,
    candidate_value_promoted_to_materialized_value: bool = False,
    accepted_source_packet_required: bool = False,
    owner_internal_policy_required: bool = False,
    owner_internal_policy_present: bool = False,
) -> dict[str, Any]:
    quantum_class = _quantum_class(record)
    record.update(
        {
            "acceptance_decision": acceptance_decision,
            "materialization_decision": materialization_decision,
            "materialization_allowed": True,
            "materialized_value": materialized_value,
            "materialized_value_type": materialized_value_type,
            "materialized_value_unit": materialized_value_unit,
            "materialized_value_scale": materialized_value_scale,
            "materialized_value_source_class": materialized_value_source_class,
            "materialized_value_authority_class": materialized_value_authority_class,
            "materialized_value_authority_ref": materialized_value_authority_ref,
            "materialized_value_source_path": materialized_value_source_path,
            "materialized_value_source_record_key": materialized_value_source_record_key,
            "materialized_value_source_field_path": materialized_value_source_field_path,
            "official_source_locator": official_source_locator,
            "quote_span_or_machine_field_locator": quote_span_or_machine_field_locator,
            "candidate_value_present_upstream": candidate_value_present_upstream,
            "candidate_value_promoted_to_materialized_value": (
                candidate_value_promoted_to_materialized_value
            ),
            "accepted_source_packet_required": accepted_source_packet_required,
            "owner_internal_policy_required": owner_internal_policy_required,
            "owner_internal_policy_present": owner_internal_policy_present,
            "materialization_block_code": None,
            "materialization_block_reason": None,
            "missing_fields": [],
            "required_next_task": "NONE_VALUE_MATERIALIZED",
            "required_next_pr_or_phase": "NONE_VALUE_MATERIALIZED",
            "responsible_authority": "PR154_OWNER_AUTHORIZED_MATERIALIZATION_BRIDGE",
            "required_input_artifact": "NONE_VALUE_MATERIALIZED",
            "exact_unblock_condition": "VALUE_ALREADY_MATERIALIZED_IN_PR154_LEDGER",
            "materialization_retry_route": "NONE_VALUE_MATERIALIZED",
            "codex_actionable_completion_steps": [],
            "atomicrows_compatibility_class": (
                tx.ATOMICROWS_COMPAT_MATERIALIZED_LEDGER_ONLY
            ),
            "atomicrows_row_materialization_status": (
                tx.ATOMICROWS_ROW_STATUS_MATERIALIZED_LEDGER_ONLY
            ),
            "agent_consumption_readiness_class": tx.AGENT_CONSUMABLE_DEFAULT_READY,
            "agent_consumption_block_reason": None,
            "low_latency_hot_path_eligibility": (
                tx.LOW_LATENCY_READY_FOR_PR155_PRECOMPUTED_REGISTRY
            ),
            "quantum_forward_compatibility_class": quantum_class,
            "quantum_optimizer_default_route": _quantum_route(quantum_class),
            "quantum_execution_required_before_use": (
                quantum_class == tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED
                or bool(record.get("quantum_execution_evidence_required"))
            ),
        }
    )
    return record


def _blocked_record(
    record: dict[str, Any],
    *,
    block_code: str,
    missing_fields: tuple[str, ...],
    candidate_value_present_upstream: bool = False,
    official_source_locator: Any = None,
    quote_span_or_machine_field_locator: Any = None,
    accepted_source_packet_required: bool = False,
    owner_internal_policy_required: bool = False,
) -> dict[str, Any]:
    completion = tx.completion_path(block_code)
    quantum_class = _quantum_class(record)
    record.update(
        {
            "acceptance_decision": tx.ACCEPTANCE_BLOCKED,
            "materialization_decision": block_code,
            "materialization_allowed": False,
            "materialized_value": None,
            "materialized_value_type": tx.VALUE_TYPE_NONE,
            "materialized_value_unit": tx.VALUE_UNIT_NONE,
            "materialized_value_scale": tx.VALUE_SCALE_NONE,
            "materialized_value_source_class": tx.VALUE_SOURCE_NONE,
            "materialized_value_authority_class": tx.AUTHORITY_BLOCKED,
            "materialized_value_authority_ref": None,
            "materialized_value_source_path": None,
            "materialized_value_source_record_key": None,
            "materialized_value_source_field_path": None,
            "official_source_locator": official_source_locator,
            "quote_span_or_machine_field_locator": quote_span_or_machine_field_locator,
            "candidate_value_present_upstream": candidate_value_present_upstream,
            "candidate_value_promoted_to_materialized_value": False,
            "accepted_source_packet_required": accepted_source_packet_required,
            "owner_internal_policy_required": owner_internal_policy_required,
            "owner_internal_policy_present": False,
            "materialization_block_code": block_code,
            "materialization_block_reason": completion["materialization_block_reason"],
            "missing_fields": list(dict.fromkeys(missing_fields)),
            "required_next_task": completion["required_next_task"],
            "required_next_pr_or_phase": completion["required_next_pr_or_phase"],
            "responsible_authority": completion["responsible_authority"],
            "required_input_artifact": completion["required_input_artifact"],
            "exact_unblock_condition": completion["exact_unblock_condition"],
            "materialization_retry_route": completion["materialization_retry_route"],
            "codex_actionable_completion_steps": list(
                completion["codex_actionable_completion_steps"]
            ),
            "atomicrows_compatibility_class": (
                tx.ATOMICROWS_COMPAT_UNKNOWN_FAIL_CLOSED
                if block_code == tx.BLOCKED_UNKNOWN_FAIL_CLOSED
                else tx.ATOMICROWS_COMPAT_BLOCKED_COMPLETION_PATH
            ),
            "atomicrows_row_materialization_status": (
                tx.ATOMICROWS_ROW_STATUS_BLOCKED_LEDGER_ONLY
            ),
            "agent_consumption_readiness_class": tx.BLOCK_TO_AGENT_READINESS.get(
                block_code,
                tx.AGENT_BLOCKED_UNKNOWN_FAIL_CLOSED,
            ),
            "agent_consumption_block_reason": completion["materialization_block_reason"],
            "low_latency_hot_path_eligibility": (
                tx.LOW_LATENCY_EXCLUDED_UNAUTHORIZED_OR_INCOMPLETE
            ),
            "quantum_forward_compatibility_class": quantum_class,
            "quantum_optimizer_default_route": _quantum_route(quantum_class),
            "quantum_execution_required_before_use": (
                quantum_class == tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED
                or bool(record.get("quantum_execution_evidence_required"))
            ),
        }
    )
    return record


def _candidate_locator(candidate: Mapping[str, Any]) -> str | None:
    officiality = _mapping(candidate.get("officiality_evidence"))
    for value in (
        candidate.get("source_url"),
        officiality.get("source_url"),
        candidate.get("source_locator"),
        officiality.get("source_locator"),
    ):
        if _non_empty(value):
            return _text(value)
    return None


def _candidate_missing_fields(
    candidate: Mapping[str, Any],
    pr153s_record: Mapping[str, Any],
) -> tuple[str, ...]:
    officiality = _mapping(candidate.get("officiality_evidence"))
    missing: list[str] = []
    if not _non_empty(candidate.get("official_source_class")) and not _non_empty(
        officiality.get("official_source_class")
    ):
        missing.append(tx.MISSING_OFFICIAL_SOURCE_AUTHORITY_CLASS)
    if _candidate_locator(candidate) is None:
        missing.append(tx.MISSING_OFFICIAL_SOURCE_LOCATOR)
    if not _non_empty(candidate.get("captured_candidate_text_or_value")):
        missing.append(tx.MISSING_CAPTURED_VALUE)
    if _text(candidate.get("retrieval_target_id")) != _text(pr153s_record.get("target_id")):
        missing.append(tx.MISSING_TARGET_FIELD_MATCH)
    if _text(candidate.get("target_field_path")) != _text(
        pr153s_record.get("target_field_path")
    ):
        missing.append(tx.MISSING_TARGET_FIELD_MATCH)
    if not _mapping(candidate.get("quote_span_or_machine_field_locator")):
        missing.append(tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR)
    conflict_reasons = [
        _text(reason)
        for reason in _list(candidate.get("conflict_review_reason_codes"))
        if _text(reason) != "PR153_HANDOFF_TO_PR154_ACCEPTANCE_REQUIRED"
    ]
    if conflict_reasons:
        missing.append(tx.CONFLICT_REVIEW_REQUIRED)
    if pr153s_record.get("split_or_reclassification_member"):
        missing.append(tx.SPLIT_RECLASSIFICATION_REQUIRED)
    if pr153s_record.get("private_doc_attestation_member"):
        missing.append(tx.PRIVATE_DOC_ATTESTATION_REQUIRED)
    if pr153s_record.get("owner_route_member"):
        missing.append(tx.OWNER_ROUTE_LOCATOR_REQUIRED)
    if pr153s_record.get("runtime_receipt_route_member"):
        missing.append(tx.RUNTIME_RECEIPT_REQUIRED)
    if pr153s_record.get("replay_paper_route_member"):
        missing.append(tx.REPLAY_PAPER_EVIDENCE_REQUIRED)
    if pr153s_record.get("quantum_evidence_route_member"):
        missing.append(tx.QUANTUM_EXECUTION_EVIDENCE_REQUIRED)
    return tuple(dict.fromkeys(missing))


def _materialize_candidate(
    pr153s_record: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    record = _base_record(pr153s_record)
    record["quantum_forward_compatibility_class"] = _quantum_class(pr153s_record)
    missing = _candidate_missing_fields(candidate, pr153s_record)
    locator = _candidate_locator(candidate)
    field_locator = dict(_mapping(candidate.get("quote_span_or_machine_field_locator")))
    if missing:
        return _blocked_record(
            record,
            block_code=tx.BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE,
            missing_fields=missing,
            candidate_value_present_upstream=_non_empty(
                candidate.get("captured_candidate_text_or_value")
            ),
            official_source_locator=locator,
            quote_span_or_machine_field_locator=field_locator or None,
            accepted_source_packet_required=False,
        )
    return _materialized_common(
        record,
        acceptance_decision=tx.ACCEPTANCE_OWNER_FAST_LANE,
        materialization_decision=tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE,
        materialized_value=candidate.get("captured_candidate_text_or_value"),
        materialized_value_type=tx.VALUE_TYPE_SOURCE_TEXT_LITERAL,
        materialized_value_unit=tx.VALUE_UNIT_SOURCE_TEXT_LITERAL,
        materialized_value_scale=tx.VALUE_SCALE_SOURCE_TEXT_LITERAL,
        materialized_value_source_class=(
            tx.VALUE_SOURCE_COMPLETE_OFFICIAL_SOURCE_CANDIDATE_FAST_LANE
        ),
        materialized_value_authority_class=tx.AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE,
        materialized_value_authority_ref=tx.AUTHORITY_REF_OWNER_OFFICIAL_FAST_LANE,
        materialized_value_source_path=PR153_REPORT_PATH,
        materialized_value_source_record_key=_text(candidate.get("candidate_packet_id")),
        materialized_value_source_field_path=(
            "source_capture_candidate_packets[].captured_candidate_text_or_value"
        ),
        official_source_locator=locator,
        quote_span_or_machine_field_locator=field_locator,
        candidate_value_present_upstream=True,
        candidate_value_promoted_to_materialized_value=True,
        accepted_source_packet_required=False,
    )


def _pr153r_locator(record: Mapping[str, Any]) -> Any:
    locators = _list(record.get("retrieved_official_locators"))
    if locators:
        return locators
    seeds = _list(record.get("classified_seed_url_candidates"))
    if seeds:
        return seeds
    return None


def _pr153r_missing_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    missing: list[str] = []
    if not _non_empty(record.get("source_family")):
        missing.append(tx.MISSING_OFFICIAL_SOURCE_AUTHORITY_CLASS)
    if _pr153r_locator(record) is None:
        missing.append(tx.MISSING_OFFICIAL_SOURCE_LOCATOR)
    if not _non_empty(record.get("exact_target_value_extracted")):
        missing.append(tx.MISSING_CAPTURED_VALUE)
    if not _non_empty(record.get("quote_span_locator")) and not _non_empty(
        record.get("machine_field_locator")
    ):
        missing.append(tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR)
    if record.get("target_field_scope_exact") is not True:
        missing.append(tx.MISSING_TARGET_FIELD_MATCH)
    for block_code in _list(record.get("block_codes")):
        if _text(block_code) == "BLOCK_CONFLICT_REVIEW_REQUIRED":
            missing.append(tx.CONFLICT_REVIEW_REQUIRED)
    return tuple(dict.fromkeys(missing))


def _materialize_pr153r_retry(
    pr153s_record: Mapping[str, Any],
    pr153r_record: Mapping[str, Any] | None,
) -> dict[str, Any]:
    record = _base_record(pr153s_record)
    record["quantum_forward_compatibility_class"] = _quantum_class(pr153s_record)
    retry = _mapping(pr153r_record)
    exact_value = retry.get("exact_target_value_extracted")
    if (
        retry.get("acceptance_decision") == "ACCEPTED_TARGET_FIELD_SOURCE_PACKET"
        and _non_empty(exact_value)
        and not _pr153r_missing_fields(retry)
    ):
        return _materialized_common(
            record,
            acceptance_decision=tx.ACCEPTANCE_EXISTING_ACCEPTED_SOURCE,
            materialization_decision=tx.MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE,
            materialized_value=exact_value,
            materialized_value_type=tx.VALUE_TYPE_SOURCE_TEXT_LITERAL,
            materialized_value_unit=tx.VALUE_UNIT_SOURCE_TEXT_LITERAL,
            materialized_value_scale=tx.VALUE_SCALE_SOURCE_TEXT_LITERAL,
            materialized_value_source_class=tx.VALUE_SOURCE_EXISTING_ACCEPTED_SOURCE_PACKET,
            materialized_value_authority_class=tx.AUTHORITY_EXISTING_ACCEPTED_SOURCE_PACKET,
            materialized_value_authority_ref="PR153R_ACCEPTED_TARGET_FIELD_SOURCE_PACKET",
            materialized_value_source_path=PR153R_REPORT_PATH,
            materialized_value_source_record_key=_text(retry.get("retrieval_target_id")),
            materialized_value_source_field_path="per_target_records[].exact_target_value_extracted",
            official_source_locator=_pr153r_locator(retry),
            quote_span_or_machine_field_locator={
                "quote_span_locator": retry.get("quote_span_locator"),
                "machine_field_locator": retry.get("machine_field_locator"),
            },
            candidate_value_present_upstream=True,
            candidate_value_promoted_to_materialized_value=True,
            accepted_source_packet_required=False,
        )
    missing = _pr153r_missing_fields(retry) or (
        tx.MISSING_CAPTURED_VALUE,
        tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR,
    )
    return _blocked_record(
        record,
        block_code=tx.BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW,
        missing_fields=missing,
        candidate_value_present_upstream=_non_empty(exact_value),
        official_source_locator=_pr153r_locator(retry),
        quote_span_or_machine_field_locator={
            "quote_span_locator": retry.get("quote_span_locator"),
            "machine_field_locator": retry.get("machine_field_locator"),
        },
        accepted_source_packet_required=True,
    )


def _materialize_internal_policy(pr153s_record: Mapping[str, Any]) -> dict[str, Any]:
    record = _base_record(pr153s_record)
    record["quantum_forward_compatibility_class"] = _quantum_class(pr153s_record)
    return _materialized_common(
        record,
        acceptance_decision=tx.ACCEPTANCE_OWNER_INTERNAL_POLICY,
        materialization_decision=(
            tx.MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT
        ),
        materialized_value=tx.OWNER_INTERNAL_POLICY_DEFAULT_VALUE,
        materialized_value_type=tx.VALUE_TYPE_OWNER_INTERNAL_POLICY_STATUS,
        materialized_value_unit=tx.VALUE_UNIT_INTERNAL_POLICY_STATUS,
        materialized_value_scale=tx.VALUE_SCALE_INTERNAL_POLICY_STATUS,
        materialized_value_source_class=tx.VALUE_SOURCE_OWNER_INTERNAL_POLICY_DEFAULT,
        materialized_value_authority_class=tx.AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT,
        materialized_value_authority_ref=tx.AUTHORITY_REF_OWNER_INTERNAL_POLICY,
        materialized_value_source_path=tx.TAXONOMY_MODULE_PATH,
        materialized_value_source_record_key=tx.OWNER_INTERNAL_POLICY_DEFAULT_KEY,
        materialized_value_source_field_path=tx.OWNER_INTERNAL_POLICY_DEFAULT_SOURCE_FIELD,
        owner_internal_policy_required=True,
        owner_internal_policy_present=True,
    )


def _owner_route_exact_value(owner_queue: Mapping[str, Any]) -> Any:
    for key in (
        "owner_provided_value",
        "owner_exact_value",
        "captured_candidate_text_or_value",
        "target_value",
    ):
        if _non_empty(owner_queue.get(key)):
            return owner_queue.get(key)
    return None


def _owner_route_missing_fields(owner_queue: Mapping[str, Any]) -> tuple[str, ...]:
    value = _owner_route_exact_value(owner_queue)
    missing: list[str] = []
    if not _non_empty(value):
        missing.append(tx.MISSING_CAPTURED_VALUE)
    if not any(
        _non_empty(owner_queue.get(key))
        for key in ("source_url", "official_source_locator", "source_locator")
    ):
        missing.append(tx.MISSING_OFFICIAL_SOURCE_LOCATOR)
    if not _non_empty(owner_queue.get("target_field_match_status")):
        missing.append(tx.MISSING_TARGET_FIELD_MATCH)
    if not any(
        _non_empty(owner_queue.get(key))
        for key in ("quote_span_locator", "machine_field_locator")
    ):
        missing.append(tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR)
    if not _non_empty(owner_queue.get("unit_or_scale_if_present")):
        missing.append(tx.MISSING_UNIT_OR_SCALE)
    missing.append(tx.OWNER_ROUTE_LOCATOR_REQUIRED)
    return tuple(dict.fromkeys(missing))


def _materialize_owner_route(
    pr153s_record: Mapping[str, Any],
    owner_queue: Mapping[str, Any] | None,
) -> dict[str, Any]:
    record = _base_record(pr153s_record)
    record["quantum_forward_compatibility_class"] = _quantum_class(pr153s_record)
    owner = _mapping(owner_queue)
    value = _owner_route_exact_value(owner)
    exact_locator = (
        owner.get("source_url")
        or owner.get("official_source_locator")
        or owner.get("source_locator")
    )
    quote_locator = {
        "quote_span_locator": owner.get("quote_span_locator"),
        "machine_field_locator": owner.get("machine_field_locator"),
    }
    missing = _owner_route_missing_fields(owner)
    if value and not missing:
        return _materialized_common(
            record,
            acceptance_decision=tx.ACCEPTANCE_OWNER_FAST_LANE,
            materialization_decision=tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE,
            materialized_value=value,
            materialized_value_type=tx.VALUE_TYPE_SOURCE_TEXT_LITERAL,
            materialized_value_unit=tx.VALUE_UNIT_SOURCE_TEXT_LITERAL,
            materialized_value_scale=tx.VALUE_SCALE_SOURCE_TEXT_LITERAL,
            materialized_value_source_class=(
                tx.VALUE_SOURCE_COMPLETE_OFFICIAL_SOURCE_CANDIDATE_FAST_LANE
            ),
            materialized_value_authority_class=(
                tx.AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE
            ),
            materialized_value_authority_ref=tx.AUTHORITY_REF_OWNER_OFFICIAL_FAST_LANE,
            materialized_value_source_path=PR153_REPORT_PATH,
            materialized_value_source_record_key=_text(owner.get("retrieval_target_id")),
            materialized_value_source_field_path="owner_blocker_decision_layer.owner_decision_required_queue[].owner_provided_value",
            official_source_locator=exact_locator,
            quote_span_or_machine_field_locator=quote_locator,
            candidate_value_present_upstream=True,
            candidate_value_promoted_to_materialized_value=True,
        )
    return _blocked_record(
        record,
        block_code=tx.BLOCKED_PENDING_OWNER_ROUTE_PACKET,
        missing_fields=missing,
        candidate_value_present_upstream=_non_empty(value),
        official_source_locator=exact_locator,
        quote_span_or_machine_field_locator=quote_locator,
        accepted_source_packet_required=True,
    )


def _blocked_from_lane(pr153s_record: Mapping[str, Any], block_code: str) -> dict[str, Any]:
    missing_by_block = {
        tx.BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION: (
            tx.SPLIT_RECLASSIFICATION_REQUIRED,
        ),
        tx.BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION: (
            tx.PRIVATE_DOC_ATTESTATION_REQUIRED,
        ),
        tx.BLOCKED_PENDING_RUNTIME_RECEIPT: (tx.RUNTIME_RECEIPT_REQUIRED,),
        tx.BLOCKED_PENDING_REPLAY_PAPER_REVIEW: (tx.REPLAY_PAPER_EVIDENCE_REQUIRED,),
        tx.BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE: (
            tx.QUANTUM_EXECUTION_EVIDENCE_REQUIRED,
        ),
        tx.BLOCKED_UNKNOWN_FAIL_CLOSED: (tx.INTERNAL_OWNER_POLICY_VALUE_REQUIRED,),
    }
    record = _base_record(pr153s_record)
    record["quantum_forward_compatibility_class"] = _quantum_class(pr153s_record)
    return _blocked_record(
        record,
        block_code=block_code,
        missing_fields=missing_by_block.get(block_code, (tx.MISSING_CAPTURED_VALUE,)),
        accepted_source_packet_required=block_code
        in {
            tx.BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION,
            tx.BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION,
        },
    )


def materialize_records(repo_root: str | Path) -> tuple[list[dict[str, Any]], inputs.PR154Inputs]:
    loaded = inputs.load_inputs(repo_root)
    upstream = loaded.pr153s_upstream
    records: list[dict[str, Any]] = []
    for pr153s_record in loaded.pr153s_records:
        target_id = _text(pr153s_record.get("target_id"))
        lane = _text(pr153s_record.get("closure_lane"))
        if lane == pr153s_tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE:
            records.append(
                _materialize_candidate(
                    pr153s_record,
                    _mapping(upstream.pr153_candidates_by_id.get(target_id)),
                )
            )
        elif lane == pr153s_tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE:
            records.append(
                _materialize_pr153r_retry(
                    pr153s_record,
                    upstream.pr153r_records_by_id.get(target_id),
                )
            )
        elif lane == pr153s_tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY:
            records.append(
                _materialize_pr153r_retry(
                    pr153s_record,
                    upstream.pr153r_records_by_id.get(target_id),
                )
            )
        elif lane == pr153s_tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE:
            records.append(_materialize_internal_policy(pr153s_record))
        elif lane == pr153s_tx.CLOSURE_OWNER_PROVIDED_ROUTE_REQUIRED:
            records.append(
                _materialize_owner_route(
                    pr153s_record,
                    upstream.pr153_owner_queue_by_id.get(target_id),
                )
            )
        elif lane == pr153s_tx.CLOSURE_SPLIT_OR_RECLASSIFICATION_REQUIRED:
            records.append(
                _blocked_from_lane(
                    pr153s_record,
                    tx.BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION,
                )
            )
        elif lane == pr153s_tx.CLOSURE_PRIVATE_DOC_ATTESTATION_REQUIRED:
            records.append(
                _blocked_from_lane(
                    pr153s_record,
                    tx.BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION,
                )
            )
        elif lane == pr153s_tx.CLOSURE_BLOCKED_UNTIL_RUNTIME_RECEIPT:
            records.append(_blocked_from_lane(pr153s_record, tx.BLOCKED_PENDING_RUNTIME_RECEIPT))
        elif lane == pr153s_tx.CLOSURE_BLOCKED_UNTIL_REPLAY_PAPER_REVIEW:
            records.append(_blocked_from_lane(pr153s_record, tx.BLOCKED_PENDING_REPLAY_PAPER_REVIEW))
        elif lane == pr153s_tx.CLOSURE_BLOCKED_UNTIL_QUANTUM_EXECUTION_EVIDENCE:
            records.append(
                _blocked_from_lane(
                    pr153s_record,
                    tx.BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE,
                )
            )
        else:
            records.append(_blocked_from_lane(pr153s_record, tx.BLOCKED_UNKNOWN_FAIL_CLOSED))
    return sorted(records, key=record_sort_key), loaded


def count_by(records: list[Mapping[str, Any]], field: str, universe: tuple[str, ...]) -> dict[str, int]:
    counter = Counter(_text(record.get(field)) for record in records)
    return {key: counter.get(key, 0) for key in universe}
