"""Scoring/ranking source readiness metadata for PR159."""

from __future__ import annotations

from typing import Any, Mapping


def build_scoring_ranking_updates(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": record["row_id"],
            "scoring_ranking_source_ready_flag": record["accepted_source_packet_ref_or_null"] is not None,
            "metadata_only_no_scoring_execution": True,
            "scoring_execution_created": False,
            "ranking_execution_created": False,
            "selection_execution_created": False,
        }
        for record in sorted(records, key=lambda item: item["row_id"])
    ]

