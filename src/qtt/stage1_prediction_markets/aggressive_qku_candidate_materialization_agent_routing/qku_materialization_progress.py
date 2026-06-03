"""Materialization progress records."""

from __future__ import annotations

from typing import Any

from .deterministic_id import deterministic_id


def materialization_progress_records(field_fills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "progress_id": deterministic_id(
                "PR162D-MATERIALIZATION-PROGRESS", record["qku_id"], size=10
            ),
            "qku_id": record["qku_id"],
            "field_fill_ref": record["field_fill_id"],
            "candidate_materialization_state": record["field_fill_status"],
            "formula_or_algorithm_route_ready_flag": True,
            "feature_builder_route_ready_flag": True,
            "replay_paper_route_ready_flag": True,
            "owner_review_optional_flag": True,
            "live_order_authority": False,
        }
        for record in field_fills
    ]
