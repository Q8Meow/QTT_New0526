from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    ACTIVE_STAGE1_VENUES,
    REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER,
    REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION,
    REJECTED_MISSING_REDACTION_ATTESTATION,
    REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_SECRET_CAPTURE_ATTEMPT,
    REJECTED_STALE_PRIVATE_STATE_RECEIPT,
    REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT,
    REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD,
    SHARED_SCOPE_METADATA,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.validator import (
    ACCOUNT_REPORT_PATH,
    GATE_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    LINKAGE_REPORT_PATH,
    MAIN_REPORT_PATH,
    REDACTION_REPORT_PATH,
    build_private_state_read_receipt_artifacts,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_private_state_read_receipt_artifacts(REPO_ROOT)


def cloned_artifacts() -> dict[str, Any]:
    return deepcopy(artifacts())


def validation_failures(value: dict[str, Any]) -> list[str]:
    return validate_artifacts(value)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def gate_report() -> dict[str, Any]:
    return artifacts()["gate_report"]


def account_report() -> dict[str, Any]:
    return artifacts()["account_report"]


def redaction_report() -> dict[str, Any]:
    return artifacts()["redaction_report"]


def linkage_report() -> dict[str, Any]:
    return artifacts()["linkage_report"]


def handoff_report() -> dict[str, Any]:
    return artifacts()["handoff_report"]


def read_requests() -> list[dict[str, Any]]:
    return gate_report()["private_state_read_requests"]


def read_receipts() -> list[dict[str, Any]]:
    return gate_report()["private_state_read_receipts"]


def rejection_receipts() -> list[dict[str, Any]]:
    return gate_report()["private_state_read_rejection_receipts"]


def account_receipts() -> list[dict[str, Any]]:
    return account_report()["account_wallet_balance_receipts"]


def redaction_attestations() -> list[dict[str, Any]]:
    return redaction_report()["private_state_redaction_attestations"]


def no_secret_attestations() -> list[dict[str, Any]]:
    return redaction_report()["private_state_no_secret_capture_attestations"]


def linkage_receipts() -> list[dict[str, Any]]:
    return linkage_report()["private_state_to_runtime_cash_linkage_receipts"]


def redacted_payloads_by_receipt() -> dict[str, dict[str, Any]]:
    return artifacts()["redacted_payloads_by_receipt"]


def stage1_venues() -> set[str]:
    return set(ACTIVE_STAGE1_VENUES)


def shared_scope_metadata() -> set[str]:
    return set(SHARED_SCOPE_METADATA)


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    paths = {
        "main_report": MAIN_REPORT_PATH,
        "gate_report": GATE_REPORT_PATH,
        "account_report": ACCOUNT_REPORT_PATH,
        "redaction_report": REDACTION_REPORT_PATH,
        "linkage_report": LINKAGE_REPORT_PATH,
        "handoff_report": HANDOFF_REPORT_PATH,
    }
    return {
        key: json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        for key, path in paths.items()
    }


REQUIRED_REJECTION_STATES = {
    REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP,
    REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER,
    REJECTED_SECRET_CAPTURE_ATTEMPT,
    REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD,
    REJECTED_MISSING_REDACTION_ATTESTATION,
    REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_PRIVATE_STATE_RECEIPT,
    REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT,
}
