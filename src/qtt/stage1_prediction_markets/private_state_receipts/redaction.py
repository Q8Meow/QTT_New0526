from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
    validate_redacted_payload_minimized,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
)


def build_redacted_payload(request: Mapping[str, object]) -> dict[str, object]:
    venue_id = str(request["venue_id"])
    payload = {
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "venue_id": venue_id,
        "platform_scope": "PREDICTION_MARKETS_GENERAL",
        "account_scope_id": str(request["account_scope_id"]),
        "wallet_scope_id": str(request["wallet_scope_id"]),
        "observed_private_state_surface": "ACCOUNT_WALLET_BALANCE",
        "redacted_components": [
            {
                "field_name": "verified_available_cash",
                "redaction_marker": "REDACTED_FIXTURE_VALUE",
                "data_type_label": "DECIMAL_STRING_REDACTED",
                "fixture_placeholder_value": "FIXTURE_PLACEHOLDER_ONLY",
            },
            {
                "field_name": "open_order_lock",
                "redaction_marker": "REDACTED_FIXTURE_VALUE",
                "data_type_label": "DECIMAL_STRING_REDACTED",
                "fixture_placeholder_value": "FIXTURE_PLACEHOLDER_ONLY",
            },
            {
                "field_name": "required_reserve",
                "redaction_marker": "REDACTED_FIXTURE_VALUE",
                "data_type_label": "DECIMAL_STRING_REDACTED",
                "fixture_placeholder_value": "FIXTURE_PLACEHOLDER_ONLY",
            },
        ],
        "retained_metadata": {
            "field_names_only": "FIELD_NAME_ONLY",
            "non_secret_digest_policy": "DIGEST_ONLY",
        },
    }
    failures = validate_redacted_payload_minimized(payload)
    if failures:
        raise ValueError("; ".join(failures))
    return payload


def redaction_attestation_id(receipt_id: str) -> str:
    return f"{receipt_id}_REDACTION_ATTESTATION_V1"


def no_secret_capture_attestation_id(receipt_id: str) -> str:
    return f"{receipt_id}_NO_SECRET_CAPTURE_ATTESTATION_V1"


def build_redaction_attestation(
    *, receipt_id: str, redacted_payload: Mapping[str, object]
) -> dict[str, object]:
    digest = canonical_redacted_payload_digest(redacted_payload)
    return {
        "redaction_attestation_id": redaction_attestation_id(receipt_id),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "redaction_attestation_state": READY_STATE,
        "private_state_read_receipt_id": receipt_id,
        "redaction_policy_id": "PR130_REDACTION_POLICY_FIELD_NAMES_MARKERS_DIGESTS_ONLY_V1",
        "redacted_fields": [
            "account_private_state_identifiers",
            "wallet_private_state_identifiers",
            "balance_component_values",
            "private_state_payload_body",
        ],
        "retained_fields": [
            "field_name",
            "redaction_marker",
            "data_type_label",
            "fixture_placeholder_value",
            "non_secret_digest",
        ],
        "redacted_payload_digest": digest,
        "canonicalized_redacted_payload_digest": digest,
        "canonicalization_policy_id": "PR130_CANONICAL_JSON_SORT_KEYS_COMPACT_UTF8_SHA256_V1",
        "raw_payload_stored_flag": False,
        "secret_like_value_detected_flag": False,
        "unredacted_private_payload_detected_flag": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }


def build_no_secret_capture_attestation(
    *, receipt_id: str, credential_placeholder: str
) -> dict[str, object]:
    return {
        "no_secret_capture_attestation_id": no_secret_capture_attestation_id(receipt_id),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "no_secret_capture_state": READY_STATE,
        "private_state_read_receipt_id": receipt_id,
        "credential_alias_placeholder_ref": credential_placeholder,
        "credential_secret_capture_allowed_flag": False,
        "credential_alias_authority_created": False,
        "credential_readiness_authority_created": False,
        "raw_api_key_stored_flag": False,
        "raw_bearer_token_stored_flag": False,
        "raw_oauth_token_stored_flag": False,
        "raw_token_stored_flag": False,
        "raw_cookie_stored_flag": False,
        "raw_wallet_secret_stored_flag": False,
        "raw_private_key_stored_flag": False,
        "raw_session_identifier_stored_flag": False,
        "secret_like_value_detected_flag": False,
        "production_credential_authority_created": False,
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
