"""No-orphan candidate audit."""

from __future__ import annotations

from typing import Any


def no_orphan_candidate_records(classifications: list[dict[str, Any]], expected_count: int) -> list[dict[str, Any]]:
    classified_ids = {row["candidate_id"] for row in classifications}
    return [
        {
            "audit_id": "PR162R_A_NO_ORPHAN_CANDIDATE",
            "candidate_source_count": expected_count,
            "classified_unique_candidate_count": len(classified_ids),
            "orphan_candidate_count": max(0, expected_count - len(classified_ids)),
            "validation_status": "PASS" if len(classified_ids) == expected_count else "FAIL",
            "live_order_authority": False,
        }
    ]
