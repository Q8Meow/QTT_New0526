"""Trade-context readiness metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "trade_context_update_id": f"PR160_TRADE_CONTEXT_UPDATE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "trade_context_readiness_impact": item["trade_context_readiness_impact"],
            "future_route": item["future_pr_route"],
            "metadata_only_no_trade_context_selection_execution": True,
            "required_actor": item["required_actor"],
            "validator_that_will_unblock": item["validator_that_will_unblock"],
        }
        for item in decisions
    ]
