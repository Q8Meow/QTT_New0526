"""No metadata-only candidate audit."""

from __future__ import annotations

from typing import Any


def no_metadata_only_candidate_audit_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metadata_only = [record["candidate_id"] for record in candidates if record.get("metadata_only_flag")]
    return [
        {
            "audit_id": "PR162D_R1_NO_METADATA_ONLY_CANDIDATE_AUDIT",
            "metadata_only_candidate_count": len(metadata_only),
            "metadata_only_candidate_ids": metadata_only,
            "validation_status": "PASS_NO_METADATA_ONLY_CANDIDATES" if not metadata_only else "FAIL",
            "live_order_authority": False,
        }
    ]
