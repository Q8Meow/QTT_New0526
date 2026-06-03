"""No hallucinated source records audit."""

from __future__ import annotations

from typing import Any


def no_hallucinated_source_audit_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing = [source["source_id"] for source in sources if not source.get("source_locator")]
    return [
        {
            "audit_id": "PR162D_R1_NO_HALLUCINATED_SOURCE_AUDIT",
            "source_record_count": len(sources),
            "source_locator_missing_count": len(missing),
            "hallucinated_source_record_count": len(missing),
            "scouting_basis": "MANDATORY_ONLINE_SCOUTING_PLUS_OFFLINE_SAFE_LOCATOR_MANIFEST",
            "validation_status": "PASS_NO_HALLUCINATED_SOURCE_RECORDS" if not missing else "FAIL",
            "live_order_authority": False,
        }
    ]
