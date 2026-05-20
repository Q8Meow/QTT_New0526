from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
)


CANONICAL_CASH_COMPONENT_NAMES = (
    "verified_available_cash",
    "open_order_lock",
    "required_reserve",
    "margin_lock",
    "unsettled_funds",
    "locked_or_withdrawal_restricted_funds",
    "pending_use_funds",
)

LINKED_CASH_COMPONENT_CLASSES = (
    "VERIFIED_AVAILABLE_CASH",
    "OPEN_ORDER_LOCK",
    "REQUIRED_RESERVE",
)


def _field_map_ids_for_venue(
    venue_id: str,
    field_maps_by_venue: Mapping[str, list[Mapping[str, object]]],
) -> list[str]:
    return [
        str(record["runtime_cash_component_field_map_id"])
        for record in field_maps_by_venue[venue_id]
    ]


def build_account_wallet_balance_receipts(
    *,
    private_state_receipts: list[Mapping[str, object]],
    field_maps_by_venue: Mapping[str, list[Mapping[str, object]]],
) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for private_receipt in private_state_receipts:
        venue_id = str(private_receipt["venue_id"])
        receipts.append(
            {
                "account_wallet_balance_receipt_id": (
                    f"PR130_{venue_id}_ACCOUNT_WALLET_BALANCE_RECEIPT_V1"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "account_wallet_balance_receipt_state": READY_STATE,
                "production_account_balance_authority": False,
                "production_wallet_balance_authority": False,
                "production_runtime_cash_receipt_authority": False,
                "private_state_read_receipt_id": private_receipt[
                    "private_state_read_receipt_id"
                ],
                "runtime_cash_component_field_map_id": private_receipt[
                    "runtime_cash_component_field_map_id"
                ],
                "venue_id": venue_id,
                "account_scope_id": private_receipt["account_scope_id"],
                "wallet_scope_id": private_receipt["wallet_scope_id"],
                "redacted_balance_component_refs": _field_map_ids_for_venue(
                    venue_id,
                    field_maps_by_venue,
                ),
                "canonical_cash_component_names": list(CANONICAL_CASH_COMPONENT_NAMES),
                "currency_codes": ["USD"],
                "amount_value_policy": "REDACTED_OR_FIXTURE_STRING_ONLY",
                "amount_value_is_production_private_state": False,
                "accepted_source_evidence_required_flag": True,
                "private_state_read_receipt_required_flag": True,
                "no_secret_capture_attestation_id": private_receipt[
                    "no_secret_capture_attestation_id"
                ],
                "redaction_attestation_id": private_receipt["redaction_attestation_id"],
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_production_launch_path_preserved": True,
            }
        )
    return receipts


def _available_receipt_ref(venue_id: str, handoff: Mapping[str, object]) -> str:
    refs = [
        str(ref)
        for ref in handoff.get("runtime_available_after_commitments_receipt_ids", [])
        if venue_id in str(ref)
    ]
    return refs[0] if refs else f"PR129_{venue_id}_AVAILABLE_AFTER_COMMITMENTS_RECEIPT_V1"


def build_linkage_receipts(
    *,
    private_state_receipts: list[Mapping[str, object]],
    account_wallet_balance_receipts: list[Mapping[str, object]],
    runtime_cash_handoff: Mapping[str, object],
) -> list[dict[str, object]]:
    account_receipts_by_private_id = {
        receipt["private_state_read_receipt_id"]: receipt
        for receipt in account_wallet_balance_receipts
    }
    linkages: list[dict[str, object]] = []
    for private_receipt in private_state_receipts:
        venue_id = str(private_receipt["venue_id"])
        account_receipt = account_receipts_by_private_id[
            private_receipt["private_state_read_receipt_id"]
        ]
        linkages.append(
            {
                "private_state_to_runtime_cash_linkage_receipt_id": (
                    f"PR130_{venue_id}_PRIVATE_STATE_TO_RUNTIME_CASH_LINKAGE_RECEIPT_V1"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "private_state_to_runtime_cash_linkage_state": READY_STATE,
                "production_runtime_cash_receipt_authority": False,
                "production_new_exposure_cash_gate_authority": False,
                "private_state_read_receipt_id": private_receipt[
                    "private_state_read_receipt_id"
                ],
                "account_wallet_balance_receipt_id": account_receipt[
                    "account_wallet_balance_receipt_id"
                ],
                "runtime_cash_component_field_map_id": private_receipt[
                    "runtime_cash_component_field_map_id"
                ],
                "runtime_available_after_commitments_receipt_ref": (
                    _available_receipt_ref(venue_id, runtime_cash_handoff)
                ),
                "linked_cash_component_classes": list(LINKED_CASH_COMPONENT_CLASSES),
                "linkage_validation_state": READY_STATE,
                "unknown_or_unreconciled_component_present_flag": False,
                "stale_private_state_receipt_present_flag": False,
                "redaction_attestation_valid_flag": True,
                "no_secret_capture_attestation_valid_flag": True,
                "production_cash_authority_allowed_flag": False,
                "order_authority_allowed_flag": False,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_runtime_resolver_snapshot_path_preserved": True,
                "future_production_launch_path_preserved": True,
            }
        )
    if {str(record["venue_id"]) for record in private_state_receipts} != set(
        ACTIVE_STAGE1_VENUES
    ):
        raise ValueError("PR130 linkages must cover exactly the three active Stage-1 venues")
    return linkages
