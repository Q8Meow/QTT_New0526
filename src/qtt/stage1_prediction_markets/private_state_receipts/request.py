from __future__ import annotations

from typing import Mapping


DETERMINISTIC_FIXTURE_TIME = "2026-05-20T00:00:00Z"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"
ACTIVE_STAGE1_VENUES = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_METADATA = ("PREDICTION_MARKETS_GENERAL",)

READY_STATE = "READY_FOR_PR130_FIXTURE_SCOPE_RECEIPT"
REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP = "REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP"
REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER = (
    "REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER"
)
REJECTED_SECRET_CAPTURE_ATTEMPT = "REJECTED_SECRET_CAPTURE_ATTEMPT"
REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD = "REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD"
REJECTED_MISSING_REDACTION_ATTESTATION = "REJECTED_MISSING_REDACTION_ATTESTATION"
REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION = (
    "REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION"
)
REJECTED_SCOPE_OR_VENUE_MISMATCH = "REJECTED_SCOPE_OR_VENUE_MISMATCH"
REJECTED_STALE_PRIVATE_STATE_RECEIPT = "REJECTED_STALE_PRIVATE_STATE_RECEIPT"
REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT = "REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT"
REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT = (
    "REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT"
)
REJECTED_NETWORK_IO_ATTEMPT = "REJECTED_NETWORK_IO_ATTEMPT"
REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT = (
    "REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT"
)
REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT = (
    "REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT"
)
REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT = "REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT"

REQUEST_PURPOSE = "PRIVATE_STATE_RECEIPT_GATE_FIXTURE_VALIDATION"
PRIVATE_STATE_SURFACE = "ACCOUNT_WALLET_BALANCE"


def account_scope_id(venue_id: str) -> str:
    return f"PR130_{venue_id}_FIXTURE_ACCOUNT_SCOPE"


def wallet_scope_id(venue_id: str) -> str:
    return f"PR130_{venue_id}_FIXTURE_WALLET_SCOPE"


def credential_alias_placeholder_ref(venue_id: str) -> str:
    return f"PR130_{venue_id}_CREDENTIAL_ALIAS_PLACEHOLDER_REQUIRES_PR113"


def primary_runtime_cash_field_map_id(venue_id: str) -> str:
    return f"PR129_{venue_id}_VERIFIED_AVAILABLE_CASH_FIELD_MAP_V1"


def common_authority_false_flags() -> dict[str, bool]:
    return {
        "account_wallet_balance_private_state_fetch_allowed_flag": False,
        "credential_secret_capture_allowed_flag": False,
        "network_io_allowed_flag": False,
        "production_connector_use_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "order_routing_authority_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
    }


def future_path_flags() -> dict[str, bool]:
    return {
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_atomicrows_bridge_path_preserved": True,
        "future_production_launch_path_preserved": True,
    }


def atomicrows_metadata() -> dict[str, object]:
    return {
        "future_atomicrows_parameter_row_refs": [],
        "future_atomicrows_family_refs": ["FUTURE_ATOMICROWS_PRIVATE_STATE_RECEIPT_FAMILY"],
        "future_atomicrows_private_state_receipt_family_ref": (
            "FUTURE_ATOMICROWS_PRIVATE_STATE_RECEIPT_FAMILY"
        ),
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
    }


def build_private_state_read_requests(
    field_maps_by_venue: Mapping[str, list[Mapping[str, object]]],
) -> list[dict[str, object]]:
    requests: list[dict[str, object]] = []
    for venue_id in ACTIVE_STAGE1_VENUES:
        field_map_id = primary_runtime_cash_field_map_id(venue_id)
        available_field_map_ids = {
            str(record["runtime_cash_component_field_map_id"])
            for record in field_maps_by_venue.get(venue_id, [])
        }
        if field_map_id not in available_field_map_ids:
            field_map_id = next(iter(sorted(available_field_map_ids)), field_map_id)
        request = {
            "private_state_read_request_id": f"PR130_{venue_id}_PRIVATE_STATE_READ_REQUEST_V1",
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "private_state_read_request_state": READY_STATE,
            "production_private_state_read_authority": False,
            "venue_id": venue_id,
            "platform_scope": "PREDICTION_MARKETS_GENERAL",
            "account_scope_id": account_scope_id(venue_id),
            "wallet_scope_id": wallet_scope_id(venue_id),
            "requested_private_state_surface": PRIVATE_STATE_SURFACE,
            "requested_field_map_ref": field_map_id,
            "runtime_cash_component_field_map_id": field_map_id,
            "credential_alias_placeholder_ref": credential_alias_placeholder_ref(venue_id),
            "credential_alias_required_future_pr": "PR113",
            "credential_alias_authority_created": False,
            "raw_secret_capture_allowed_flag": False,
            "request_purpose": REQUEST_PURPOSE,
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            "future_production_launch_path_preserved": True,
        }
        request.update(common_authority_false_flags())
        request.update(atomicrows_metadata())
        requests.append(request)
    return requests
