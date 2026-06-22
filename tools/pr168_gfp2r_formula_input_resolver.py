#!/usr/bin/env python3
"""Input resolver facade for PR168-GFP2R formula execution."""

from __future__ import annotations

from typing import Any


def resolved_inputs_for_variant(variant: dict[str, Any]) -> dict[str, Any]:
    context = variant.get("market_context", {})
    values = dict(variant.get("available_input_values", {}))
    values["snapshot_refs"] = context.get("snapshot_refs", [])
    values["feature_refs"] = context.get("feature_refs", [])
    values["data_quality_score_non_proof"] = context.get("data_quality_score_non_proof")
    values["data_sufficiency_tier"] = context.get("data_sufficiency_tier")
    return values
