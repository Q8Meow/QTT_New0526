"""PR158 selection-readiness metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "selection_update_id": f"PR160_SELECTION_UPDATE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "split_dependency_resolved_flag": True,
            "split_dependency_route_closed_flag": True,
            "final_route_class": item["final_route_class"],
            "scoring_readiness_impact": item["selection_readiness_impact"],
            "trade_context_readiness_impact": item["trade_context_readiness_impact"],
            "low_latency_precomputed_index_eligibility_impact": item["low_latency_index_impact"],
            "quantum_classical_compatibility": item["quantum_classical_compatibility"],
            "metadata_only_no_selection_execution": True,
            "can_qtt_use_in_replay_flag": False,
            "can_qtt_use_in_paper_flag": False,
            "can_qtt_use_in_live_flag": False,
        }
        for item in decisions
    ]
