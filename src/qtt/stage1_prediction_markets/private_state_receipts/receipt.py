from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.redaction import (
    no_secret_capture_attestation_id,
    redaction_attestation_id,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
    common_authority_false_flags,
    future_path_flags,
)


def receipt_id_for_request(request: Mapping[str, object]) -> str:
    return str(request["private_state_read_request_id"]).replace(
        "_REQUEST_V1", "_RECEIPT_V1"
    )


def build_private_state_read_receipt(
    *, request: Mapping[str, object], redacted_payload: Mapping[str, object]
) -> dict[str, object]:
    receipt_id = receipt_id_for_request(request)
    digest = canonical_redacted_payload_digest(redacted_payload)
    receipt = {
        "private_state_read_receipt_id": receipt_id,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "private_state_read_receipt_state": READY_STATE,
        "production_private_state_read_authority": False,
        "production_account_balance_authority": False,
        "production_wallet_balance_authority": False,
        "production_runtime_cash_receipt_authority": False,
        "private_state_read_request_id": request["private_state_read_request_id"],
        "venue_id": request["venue_id"],
        "platform_scope": request["platform_scope"],
        "account_scope_id": request["account_scope_id"],
        "wallet_scope_id": request["wallet_scope_id"],
        "runtime_cash_component_field_map_id": request["runtime_cash_component_field_map_id"],
        "observed_private_state_surface": request["requested_private_state_surface"],
        "redacted_payload_digest": digest,
        "canonicalized_redacted_payload_digest": digest,
        "redaction_attestation_id": redaction_attestation_id(receipt_id),
        "no_secret_capture_attestation_id": no_secret_capture_attestation_id(receipt_id),
        "credential_alias_placeholder_ref": request["credential_alias_placeholder_ref"],
        "credential_alias_required_future_pr": "PR113",
        "credential_alias_authority_created": False,
        "private_state_receipt_status": READY_STATE,
        "receipt_staleness_policy": "REJECT_IF_STALE_OR_SUPERSEDED_FIXTURE_RECEIPT",
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    receipt.update(common_authority_false_flags())
    receipt.update(future_path_flags())
    return receipt
