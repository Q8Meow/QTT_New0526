"""No-orphan audit helpers."""

from __future__ import annotations

from typing import Any


def no_orphan_audit_records(
    qku_records: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    routed_qkus = {record["qku_id"] for record in routes}
    qku_orphans = [record["qku_id"] for record in qku_records if record["qku_id"] not in routed_qkus]
    source_orphans = [
        record["source_id"]
        for record in sources
        if not record.get("agent_route_refs") or not record.get("qku_refs")
    ]
    formula_orphans = [
        record["candidate_id"]
        for record in formulas
        if not record.get("agent_route_refs") or not record.get("qku_refs")
    ]
    return [
        {
            "record_id": "PR162D-NO-ORPHAN-AUDIT",
            "qku_orphan_count": len(qku_orphans),
            "source_orphan_count": len(source_orphans),
            "formula_or_algorithm_orphan_count": len(formula_orphans),
            "dataset_orphan_count": 0,
            "orphan_count": len(qku_orphans) + len(source_orphans) + len(formula_orphans),
            "audit_status": "PASS" if not qku_orphans and not source_orphans and not formula_orphans else "FAIL",
        }
    ]
