"""PR158 owner response validation."""

from __future__ import annotations

from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge.owner_input_validator import (
    validate_owner_response_payload as validate_pr157_owner_response_payload,
)

from . import constants as c
from .io import as_list, as_mapping


def validate_owner_response_payload(
    response_payload: Mapping[str, Any],
    request_packet: Mapping[str, Any],
) -> tuple[str, ...]:
    failures = list(validate_pr157_owner_response_payload(response_payload, request_packet))
    request_map = {
        str(item.get("request_id")): as_mapping(item)
        for item in as_list(request_packet.get("requests"))
        if item.get("request_id")
    }
    for raw_item in as_list(response_payload.get("response_items")):
        item = as_mapping(raw_item)
        request_id = str(item.get("request_id") or "")
        request = request_map.get(request_id, {})
        if item.get("claims_external_fact") is True:
            failures.append(f"PR158_OWNER_RESPONSE_EXTERNAL_FACT_FORBIDDEN:{request_id}")
        if request.get("private_document_access_authorization_required_flag") is True:
            failures.append(f"PR158_OWNER_RESPONSE_PRIVATE_DOC_COMPLETION_FORBIDDEN_WITHOUT_DECISION:{request_id}")
        if request.get("requested_value_type") == "INTERNAL_POLICY_METADATA":
            value = item.get("value")
            if isinstance(value, (int, float)):
                failures.append(f"PR158_OWNER_RESPONSE_NUMERIC_RANGE_INVENTED:{request_id}")
        for flag in (
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
        ):
            if item.get(flag) is True:
                failures.append(f"PR158_OWNER_RESPONSE_FORBIDDEN_AUTHORITY:{request_id}:{flag}")
    return tuple(sorted(set(failures)))
