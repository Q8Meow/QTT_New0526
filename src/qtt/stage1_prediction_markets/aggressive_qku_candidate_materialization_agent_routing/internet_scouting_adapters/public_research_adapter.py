"""Public research scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-PUBLIC-RESEARCH", "TIER_3", "PUBLIC_RESEARCH_FORMULA")
