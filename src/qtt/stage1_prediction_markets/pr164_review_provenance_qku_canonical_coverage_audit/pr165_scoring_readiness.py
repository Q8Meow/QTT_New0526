"""PR165 scoring readiness routing."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_pr165_scoring_readiness_rows(
    computability_rows: list[dict[str, Any]],
    infra_by_candidate: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(computability_rows, 1):
        infra = infra_by_candidate.get(row["candidate_id"], {})
        blocked = (not row["candidate_id"]) or infra.get("artificial_infrastructure_rejection_flag", False)
        rows.append(
            {
                "pr165_scoring_readiness_ref": plain_ref("PR165_READY", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "review_status": (
                    "REVIEW_REPAIR_REQUIRED_BEFORE_PR165"
                    if blocked
                    else "REVIEW_READY_FOR_PR165"
                ),
                "pr165_scoring_ready_flag": not blocked,
                "pr165_scoring_blocked_flag": blocked,
                "exact_block_reason": (
                    "candidate_packet_or_infrastructure_repair_required"
                    if blocked
                    else ""
                ),
                "downstream_pr_route": (
                    "ROUTE_TO_PR163_C_INFRA_REPAIR"
                    if infra.get("artificial_infrastructure_rejection_flag", False)
                    else (
                        "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
                        if not row["candidate_id"]
                        else "ROUTE_TO_PR165_SCORING"
                    )
                ),
                "validation_status": "PASS",
            }
        )
    return rows
