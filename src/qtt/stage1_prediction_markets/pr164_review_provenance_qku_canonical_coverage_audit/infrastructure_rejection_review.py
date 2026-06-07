"""PR163-B infrastructure rejection review."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


ARTIFICIAL_INFRA_FAMILIES = {
    "PAPER_ADAPTER_REPAIR",
    "REPLAY_ADAPTER_REPAIR",
}


def build_infrastructure_rejection_rows(remediation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(sorted(remediation_rows, key=lambda item: item["candidate_packet_id"]), 1):
        artificial = row.get("remediation_family") in ARTIFICIAL_INFRA_FAMILIES or row.get("repairability") == "REPAIRABLE_PRE_LAUNCH"
        rows.append(
            {
                "infrastructure_rejection_review_ref": plain_ref("INFRA_REJECTION", index),
                "candidate_id": row["candidate_packet_id"],
                "qku_ids": row.get("qku_ids") or [],
                "remediation_ref": row.get("remediation_ref", ""),
                "paper_pretrade_status": row.get("paper_pretrade_status", ""),
                "replay_pretrade_status": row.get("replay_pretrade_status", ""),
                "remediation_family": row.get("remediation_family", ""),
                "repairability": row.get("repairability", ""),
                "artificial_infrastructure_rejection_flag": artificial,
                "exact_repair_action": row.get("exact_repair_action", ""),
                "downstream_pr_route": "ROUTE_TO_PR163_C_INFRA_REPAIR" if artificial else "ROUTE_TO_PR165_SCORING",
                "no_forced_pass": row.get("no_forced_pass", True),
                "validation_status": "PASS",
            }
        )
    return rows
