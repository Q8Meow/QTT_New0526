from __future__ import annotations

from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.credential_readiness import policy


def build_secret_no_capture_attestations(
    alias_records: list[Mapping[str, Any]],
) -> list[dict[str, object]]:
    attestations: list[dict[str, object]] = []
    for record in alias_records:
        alias_id = str(record["credential_alias_id"])
        attestations.append(
            {
                **policy.common_record_fields("SECRET_NO_CAPTURE_ATTESTATION"),
                "attestation_id": f"{alias_id}_NO_CAPTURE_ATTESTATION_V1",
                "scanned_artifact_refs": [
                    "src/qtt/stage1_prediction_markets/credential_readiness/",
                    "tools/credential_alias_secret_no_capture_readiness_validate.py",
                    "tests/fixtures/source_evidence/pr131_credential_alias_secret_no_capture/",
                ],
                "rejected_secret_like_classes": list(policy.SECRET_LIKE_REJECTION_CLASSES),
                "raw_secret_capture_detected": False,
                "raw_secret_hash_created": False,
                "secret_like_value_hashed": False,
                "redaction_required": True,
                "redaction_completed_for_fixture_secret_like_examples": True,
                "credential_provider_called": False,
                "environment_variable_read": False,
                "secret_manager_called": False,
                "network_io_created": False,
                "logs_contain_raw_secret": False,
                "reports_contain_raw_secret": False,
                "fixture_contains_raw_secret": False,
                "production_secret_materialized": False,
                "alias_registry_ref": alias_id,
            }
        )
    return attestations


def build_rejection_receipts() -> list[dict[str, object]]:
    return [
        {
            **policy.common_record_fields("CREDENTIAL_READINESS_REJECTION_RECEIPT"),
            "rejection_id": f"PR131_SECRET_LIKE_REJECTION_{index:02d}_{rejection_class}",
            "rejected_class": rejection_class,
            "rejected_reason_code": f"BLOCKED_{rejection_class}",
            "rejected_artifact_ref": "PR131_REDACTED_SECRET_LIKE_PAYLOAD_CLASS_LABEL_FIXTURE",
            "raw_value_stored": False,
            "raw_value_printed": False,
            "raw_value_hashed": False,
            "redacted_placeholder_used": True,
            "validator_fail_closed": True,
        }
        for index, rejection_class in enumerate(
            policy.SECRET_LIKE_REJECTION_CLASSES,
            start=1,
        )
    ]


def validate_no_capture_attestations(attestations: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    for attestation in attestations:
        if tuple(attestation.get("rejected_secret_like_classes", [])) != policy.SECRET_LIKE_REJECTION_CLASSES:
            failures.append("no-capture attestation must enumerate centralized rejection classes")
        for flag in (
            "raw_secret_capture_allowed",
            "raw_secret_capture_detected",
            "raw_secret_hashing_allowed",
            "raw_secret_hash_created",
            "secret_like_value_hashed",
            "credential_provider_called",
            "environment_variable_read",
            "secret_manager_called",
            "network_io_created",
            "logs_contain_raw_secret",
            "reports_contain_raw_secret",
            "fixture_contains_raw_secret",
            "production_secret_materialized",
        ):
            if attestation.get(flag) is not False:
                failures.append(f"no-capture attestation {flag} must be false")
        if attestation.get("redaction_required") is not True:
            failures.append("redaction is required for secret-like fixture labels")
        if attestation.get("redaction_completed_for_fixture_secret_like_examples") is not True:
            failures.append("redaction must be completed for symbolic examples")
    return failures


def validate_rejection_receipts(receipts: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    classes = {record.get("rejected_class") for record in receipts}
    if classes != set(policy.SECRET_LIKE_REJECTION_CLASSES):
        failures.append("rejection receipts must cover every centralized secret-like class")
    for receipt in receipts:
        for flag in ("raw_value_stored", "raw_value_printed", "raw_value_hashed"):
            if receipt.get(flag) is not False:
                failures.append(f"rejection receipt {flag} must be false")
        if receipt.get("redacted_placeholder_used") is not True:
            failures.append("rejection receipt must use redacted placeholder")
        if receipt.get("validator_fail_closed") is not True:
            failures.append("rejection receipt must be fail-closed")
    return failures
