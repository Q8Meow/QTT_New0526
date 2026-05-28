"""Scoring/ranking readiness metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "scoring_ranking_update_id": f"PR160_SCORING_RANKING_UPDATE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "can_qtt_use_in_scoring_metadata_flag": item["can_qtt_use_in_scoring_metadata_flag"],
            "scoring_readiness_impact": item["selection_readiness_impact"],
            "future_route": item["future_pr_route"],
            "metadata_only_no_scoring_execution": True,
            "metadata_only_no_ranking_execution": True,
            "metadata_only_no_selection_execution": True,
        }
        for item in decisions
    ]
