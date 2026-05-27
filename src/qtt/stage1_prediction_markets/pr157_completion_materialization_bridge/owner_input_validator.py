"""Strict owner response validation for PR157."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping


REQUIRED_RESPONSE_FIELDS = (
    "response_id",
    "owner_attestation_timestamp_or_declared_date",
    "owner_identity_or_alias",
    "response_items",
    "schema_version",
)
ALLOWED_OWNER_AUTHORITY_CLASSES = {
    c.AuthorityClass.OWNER_INTERNAL_POLICY.value,
    c.AuthorityClass.OWNER_PRIVATE_DOC_ATTESTATION.value,
    c.AuthorityClass.OWNER_ROUTE_DECISION.value,
    c.AuthorityClass.OWNER_EDITABLE_INTERNAL_POLICY.value,
}


def validate_owner_response_payload(
    response_payload: Mapping[str, Any],
    request_packet: Mapping[str, Any],
) -> tuple[str, ...]:
    failures: list[str] = []
    for field in REQUIRED_RESPONSE_FIELDS:
        if field not in response_payload:
            failures.append(f"PR157_OWNER_RESPONSE_MISSING_FIELD:{field}")
    request_ids = {
        str(item.get("request_id"))
        for item in as_list(request_packet.get("requests"))
        if item.get("request_id")
    }
    request_by_id = {
        str(item.get("request_id")): as_mapping(item)
        for item in as_list(request_packet.get("requests"))
        if item.get("request_id")
    }
    for index, raw_item in enumerate(as_list(response_payload.get("response_items"))):
        item = as_mapping(raw_item)
        request_id = str(item.get("request_id") or "")
        if not request_id:
            failures.append(f"PR157_OWNER_RESPONSE_ITEM_MISSING_REQUEST_ID:{index}")
            continue
        if request_id not in request_ids:
            failures.append(f"PR157_OWNER_RESPONSE_UNKNOWN_REQUEST_ID:{request_id}")
            continue
        request = request_by_id[request_id]
        has_value = "value" in item and item.get("value") not in (None, "")
        explicit_decline = item.get("explicit_decline") is True
        if has_value == explicit_decline:
            failures.append(f"PR157_OWNER_RESPONSE_VALUE_OR_DECLINE_REQUIRED:{request_id}")
        authority = str(item.get("authority_class") or "")
        if authority not in ALLOWED_OWNER_AUTHORITY_CLASSES:
            failures.append(f"PR157_OWNER_RESPONSE_BAD_AUTHORITY_CLASS:{request_id}")
        if item.get("claims_external_fact") is True:
            failures.append(f"PR157_OWNER_RESPONSE_EXTERNAL_FACT_CLAIM_FORBIDDEN:{request_id}")
        if request.get("private_document_access_authorization_required_flag") is True:
            if not item.get("attestation_text"):
                failures.append(f"PR157_OWNER_RESPONSE_PRIVATE_DOC_ATTESTATION_REQUIRED:{request_id}")
        if request.get("agent_assignment_required_flag") is True:
            value = item.get("value")
            if has_value and not isinstance(value, (str, Mapping)):
                failures.append(f"PR157_OWNER_RESPONSE_AGENT_ASSIGNMENT_TYPE_INVALID:{request_id}")
        if item.get("mutates_open_orders") is True or item.get("mutates_open_positions") is True:
            failures.append(f"PR157_OWNER_RESPONSE_OPEN_ORDER_POSITION_MUTATION:{request_id}")
        forbidden_flags = (
            "creates_runtime_authority",
            "creates_live_authority",
            "creates_replay_authority",
            "creates_paper_authority",
            "creates_scoring_execution",
            "creates_optimizer_execution",
            "creates_quantum_backend_execution",
            "creates_order_fill_profit_authority",
            "creates_qtt_checksum_freeze_global_digest_authority",
            "creates_atomicrows_bundle_checksum_hash_authority",
        )
        for flag in forbidden_flags:
            if item.get(flag) is True:
                failures.append(f"PR157_OWNER_RESPONSE_FORBIDDEN_AUTHORITY:{request_id}:{flag}")
        if request.get("requested_value_type") in {"AGENT_ASSIGNMENT_OR_PERMISSION"}:
            if has_value and isinstance(item.get("value"), str) and not item.get("owner_assignment_explicit"):
                failures.append(f"PR157_OWNER_RESPONSE_AGENT_ASSIGNMENT_CONFIRMATION_REQUIRED:{request_id}")
    return tuple(sorted(set(failures)))
