"""Formula-only and generated-derivative route updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    eligible = {
        c.ReclassificationFinalRouteClass.FORMULA_ONLY_DERIVED_ROUTE.value,
        c.ReclassificationFinalRouteClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS_ROUTE.value,
        c.ReclassificationFinalRouteClass.SCORING_RANKING_METADATA_ROUTE.value,
        c.ReclassificationFinalRouteClass.REPLAY_PAPER_EVALUATION_FUTURE_ROUTE.value,
    }
    return [
        {
            "formula_derived_route_id": f"PR160_FORMULA_DERIVED_ROUTE__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "future_route": item["future_pr_route"],
            "accepted_upstream_inputs_required_flag": item["blocker_class"]
            == c.BlockerClass.ACCEPTED_INPUTS_REQUIRED.value,
            "formula_execution_created_by_PR160_flag": False,
            "scoring_ranking_execution_created_by_PR160_flag": False,
            "optimizer_execution_created_by_PR160_flag": False,
            "validator_that_will_unblock": item["validator_that_will_unblock"],
        }
        for item in decisions
        if item["final_route_class"] in eligible
    ]
