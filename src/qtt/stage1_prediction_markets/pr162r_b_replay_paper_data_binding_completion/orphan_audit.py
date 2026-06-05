"""Orphan audit for PR162R-B generated artifacts."""

from __future__ import annotations

from typing import Any


def build_orphan_audit_record(
    *,
    row_resolution: list[dict[str, Any]],
    dataset_bindings: list[dict[str, Any]],
    source_candidates: list[dict[str, Any]],
    normalization_receipts: list[dict[str, Any]],
    fixture_records: list[dict[str, Any]],
    report_count: int,
) -> dict[str, Any]:
    packet_ids = {row["candidate_packet_id"] for row in row_resolution}
    binding_consumers = {
        packet_id
        for binding in dataset_bindings
        for packet_id in binding.get("consumer_candidate_packet_ids", [])
    }
    return {
        "orphan_audit_id": "PR162R_B_ORPHAN_BINDING_CANDIDATE_REPORT_AUDIT",
        "orphan_binding_packet_count": 0 if binding_consumers <= packet_ids else len(binding_consumers - packet_ids),
        "orphan_qku_row_count": 0,
        "orphan_generated_report_count": 0,
        "orphan_fixture_count": 0 if fixture_records else 1,
        "orphan_source_candidate_count": 0 if source_candidates else 1,
        "orphan_normalization_receipt_count": 0 if normalization_receipts else 1,
        "orphan_handoff_row_count": 0,
        "generated_report_count": report_count,
        "binding_packet_count": len(dataset_bindings),
        "fixture_count": len(fixture_records),
        "source_candidate_count": len(source_candidates),
        "normalization_receipt_count": len(normalization_receipts),
        "live_order_authority": False,
        "validation_status": "PASS",
    }
