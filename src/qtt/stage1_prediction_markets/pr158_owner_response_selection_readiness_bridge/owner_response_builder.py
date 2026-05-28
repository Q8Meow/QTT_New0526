"""Build PR157-compatible owner response items from PR158 lane records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _false_authority_flags() -> dict[str, bool]:
    return {
        "claims_external_fact": False,
        "mutates_open_orders": False,
        "mutates_open_positions": False,
        "creates_runtime_authority": False,
        "creates_live_authority": False,
        "creates_replay_authority": False,
        "creates_paper_authority": False,
        "creates_scoring_execution": False,
        "creates_optimizer_execution": False,
        "creates_quantum_backend_execution": False,
        "creates_order_fill_profit_authority": False,
        "creates_qtt_checksum_freeze_global_digest_authority": False,
        "creates_atomicrows_bundle_checksum_hash_authority": False,
    }


def _pr157_authority_for(record: Mapping[str, Any]) -> str:
    lane = record.get("lane")
    if lane == c.PR158Lane.LANE_D_PR154_OWNER_ROUTE.value:
        return "OWNER_ROUTE_DECISION"
    return "OWNER_INTERNAL_POLICY"


def response_item(record: Mapping[str, Any]) -> dict[str, Any] | None:
    value = record.get("response_value_or_null")
    if value is None:
        return None
    item = {
        "request_id": record["request_id"],
        "value": value,
        "authority_class": _pr157_authority_for(record),
        "pr158_owner_response_authority_class": record.get("owner_response_authority_class"),
        "basis_refs": list(record.get("basis_artifact_refs") or record.get("prior_route_artifact_refs") or []),
        "owner_policy_assumption_allowed_for_replay_paper_flag": True,
        "owner_policy_assumption_live_blocked_until_gates_flag": True,
        "owner_change_requires_policy_snapshot_flag": True,
        "owner_change_requires_replay_flag": True,
        "owner_change_requires_paper_flag": True,
        "owner_change_blocks_live_until_review_flag": True,
        "explicit_decline": False,
        **_false_authority_flags(),
    }
    if record.get("lane") == c.PR158Lane.LANE_A_AGENT_ASSIGNMENT.value:
        item["owner_assignment_explicit"] = True
        item["exact_agent_id_deferred_to_PR163"] = True
    return item


def build_owner_response(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    items = [item for record in records if (item := response_item(record)) is not None]
    return {
        "schema_version": "PR157_OWNER_COMPLETION_INPUT_RESPONSE_V1",
        "response_id": "PR158_OWNER_RESPONSE_MATERIALIZATION_PREVIEW_AND_RESPONSE",
        "owner_attestation_timestamp_or_declared_date": "2026-05-27",
        "owner_identity_or_alias": "Owner",
        "response_items": sorted(items, key=lambda item: item["request_id"]),
        "pr158_authority_class": c.AUTHORITY_CLASS,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }

