"""Official public docs scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-OFFICIAL-PUBLIC-DOCS", "TIER_1", "OFFICIAL_VENUE_PUBLIC_DOC")
