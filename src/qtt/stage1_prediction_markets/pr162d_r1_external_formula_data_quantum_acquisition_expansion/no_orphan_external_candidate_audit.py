"""No-orphan external candidate audit."""

from __future__ import annotations

from typing import Any


def no_orphan_external_candidate_audit_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    orphan_ids = [
        record["candidate_id"]
        for record in candidates
        if not record.get("qku_refs") or not (record.get("agent_refs") or record.get("agent_route_refs")) or not record.get("replay_paper_route_refs")
    ]
    return [
        {
            "audit_id": "PR162D_R1_NO_ORPHAN_EXTERNAL_CANDIDATE_AUDIT",
            "orphan_external_candidate_count": len(orphan_ids),
            "unrouted_external_candidate_count": len(orphan_ids),
            "orphan_candidate_ids": orphan_ids,
            "validation_status": "PASS_NO_ORPHANS" if not orphan_ids else "FAIL_ORPHANS",
            "live_order_authority": False,
        }
    ]
