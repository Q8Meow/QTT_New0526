"""Graph and source enrichment trigger plans."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_graph_enrichment_plan(identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(identity_rows, 1):
        needs = not bool(row["candidate_id"])
        rows.append(
            {
                "graph_enrichment_plan_ref": plain_ref("GRAPH_ENRICH", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "graph_pr_label_edge_enrichment_required": needs,
                "enrichment_reason": (
                    "Historical QKU lacks current CandidatePacketV1 row."
                    if needs
                    else "Current candidate has QKU and PR163-B route closure."
                ),
                "downstream_pr_route": "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR" if needs else "ROUTE_TO_PR165_SCORING",
                "validation_status": "PASS",
            }
        )
    return rows
