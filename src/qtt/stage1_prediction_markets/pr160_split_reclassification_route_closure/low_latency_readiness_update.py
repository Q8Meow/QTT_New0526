"""Low-latency precomputed-index metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "low_latency_update_id": f"PR160_LOW_LATENCY_UPDATE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "low_latency_index_impact": item["low_latency_index_impact"],
            "low_latency_precomputed_index_metadata_only_flag": True,
            "live_hot_path_authority_created_flag": False,
            "runtime_receipt_created_flag": False,
        }
        for item in decisions
    ]
