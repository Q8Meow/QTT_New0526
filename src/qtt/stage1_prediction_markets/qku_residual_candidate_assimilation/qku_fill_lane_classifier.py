"""Fill-lane classification."""

from __future__ import annotations


def classify_entity_fill_lane(entity: dict[str, object]) -> str:
    return "LANE_1"


def classify_field_value_fill_lane(field_value: dict[str, object]) -> str:
    return "LANE_0"


def classify_residual_fill_lane(residual: dict[str, object]) -> str:
    lane = str(residual.get("recommended_fill_lane") or "")
    if "MASTER_PLAN" in lane:
        return "LANE_4"
    if "OPTIMIZER" in lane:
        return "LANE_9"
    if "EXISTING_PR" in lane:
        return "LANE_7"
    if residual.get("formula_candidate_if_available"):
        return "LANE_3"
    if residual.get("range_candidate_if_available") or residual.get("value_candidate_if_available"):
        return "LANE_3"
    return "LANE_15"
