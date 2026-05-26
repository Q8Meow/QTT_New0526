"""Accepted packet validation helpers for PR153R redo."""

from __future__ import annotations

from typing import Any, Mapping

from . import taxonomy as tx


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_accepted_packet(packet: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required_text_fields = (
        "retrieval_target_id",
        "target_field_path",
        "platform_scope",
        "official_source_class",
        "official_source_locator",
        "target_value",
        "unit_scale_enum_domain",
        "target_field_scope",
        "platform_venue_scope",
        "conflict_check_status",
        "revalidation_policy",
        "source_materiality_class",
    )
    for key in required_text_fields:
        if not _has_text(packet.get(key)):
            failures.append(f"ACCEPTED_PACKET_REQUIRED_FIELD_MISSING: {key}")

    if packet.get("official_source_class") not in tx.OFFICIAL_SOURCE_CLASSES:
        failures.append(tx.BLOCK_SOURCE_NOT_OFFICIAL)

    if not (
        _has_text(packet.get("quote_span_locator"))
        or _has_text(packet.get("machine_field_locator"))
    ):
        failures.append(tx.BLOCK_MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR)

    digest_fields = [
        field
        for field in (
            "source_document_digest",
            "source_content_digest",
            "retrieval_artifact_digest",
            "source_packet_integrity_digest",
        )
        if _has_text(packet.get(field))
    ]
    if not digest_fields:
        failures.append(tx.BLOCK_MISSING_SOURCE_DIGEST)

    if packet.get("target_field_scope") != packet.get("target_field_path"):
        failures.append(tx.BLOCK_TARGET_FIELD_MISMATCH)
    if packet.get("platform_venue_scope") != packet.get("platform_scope"):
        failures.append(tx.BLOCK_SCOPE_TOO_BROAD_FOR_ACCEPTANCE)
    if packet.get("conflict_check_status") != "CLEAR":
        failures.append(tx.BLOCK_CONFLICT_REVIEW_REQUIRED)
    if not _has_text(packet.get("revalidation_policy")):
        failures.append(tx.BLOCK_REVALIDATION_POLICY_MISSING)
    if packet.get("connector_semantic_binding_created") not in (False, None):
        failures.append("ACCEPTED_PACKET_MUST_NOT_CREATE_CONNECTOR_BINDING")
    for key in (
        "runtime_cash_receipt_created",
        "order_receipt_created",
        "fill_receipt_created",
        "replay_result_created",
        "paper_result_created",
        "live_reachability_created",
        "profit_evidence_created",
        "qtt_sha_freeze_checksum_authority_created",
        "global_repository_digest_authority_created",
        "atomicrows_bundle_hash_sha_authority_created",
    ):
        if packet.get(key) not in (False, None):
            failures.append(f"ACCEPTED_PACKET_FORBIDDEN_AUTHORITY_CREATED: {key}")
    return failures


def digest_metadata_policy_failures(record: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    metadata = record.get("source_packet_digest_metadata")
    if not isinstance(metadata, Mapping):
        return [tx.BLOCK_MISSING_SOURCE_DIGEST]
    if metadata.get("scope_type") != "TARGET_FIELD_SOURCE_PROVENANCE":
        failures.append("DIGEST_METADATA_SCOPE_NOT_TARGET_FIELD_SOURCE_PROVENANCE")
    authority_class = str(metadata.get("digest_authority_class") or "")
    if "QTT" in authority_class and "NOT_QTT" not in authority_class:
        failures.append("DIGEST_METADATA_QTT_AUTHORITY_FORBIDDEN")
    if "GLOBAL" in authority_class and "NOT_GLOBAL" not in authority_class:
        failures.append("DIGEST_METADATA_GLOBAL_AUTHORITY_FORBIDDEN")
    if "ATOMICROWS" in authority_class and "NOT_ATOMICROWS" not in authority_class:
        failures.append("DIGEST_METADATA_ATOMICROWS_AUTHORITY_FORBIDDEN")
    forbidden = metadata.get("forbidden_digest_authority_classes_created")
    if forbidden not in ([], (), None):
        failures.append("DIGEST_METADATA_FORBIDDEN_AUTHORITY_CLASS_CREATED")
    allowed = set(tx.ALLOWED_DIGEST_METADATA_FIELDS) | {
        "scope_type",
        "digest_authority_class",
        "forbidden_digest_authority_classes_created",
    }
    for key in metadata:
        if key not in allowed:
            failures.append(f"DIGEST_METADATA_FIELD_NOT_ALLOWED: {key}")
    if not metadata.get("source_packet_integrity_digest"):
        failures.append(tx.BLOCK_MISSING_SOURCE_DIGEST)
    return failures
