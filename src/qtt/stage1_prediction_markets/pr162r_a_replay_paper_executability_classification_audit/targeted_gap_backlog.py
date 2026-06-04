"""Targeted PR162D-R2 critical gap backlog builders."""

from __future__ import annotations

from typing import Any


def critical_gap_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "backlog_id": f"PR162D_R2_CRITICAL_GAP::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "critical_missing_info": row["critical_missing_info"],
            "primary_executability_state": row["primary_executability_state"],
            "target_pr": "PR162D_R2",
            "live_order_authority": False,
        }
        for row in classifications
        if row.get("critical_missing_info")
    ]


def enhancement_records(classifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in classifications:
        tags = set(row.get("secondary_tags") or [])
        if tags.intersection({"NON_OFFICIAL_SOURCE", "FORMULA_DEDUPE_REVIEW_NEEDED", "OWNER_REVIEW_OPTIONAL"}):
            rows.append(
                {
                    "enhancement_id": f"PR162D_R2_OPTIONAL_ENHANCEMENT::{row['candidate_id']}",
                    "candidate_id": row["candidate_id"],
                    "enhancement_tags": sorted(tags.intersection({"NON_OFFICIAL_SOURCE", "FORMULA_DEDUPE_REVIEW_NEEDED", "OWNER_REVIEW_OPTIONAL"})),
                    "blocks_replay_paper_flag": False,
                    "target_pr": "PR162D_R2_OPTIONAL_OR_LATER",
                    "live_order_authority": False,
                }
            )
    return rows
