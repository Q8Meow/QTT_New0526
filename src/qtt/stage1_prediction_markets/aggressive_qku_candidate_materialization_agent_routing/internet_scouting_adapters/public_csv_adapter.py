"""Public CSV scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-PUBLIC-CSV", "TIER_1", "OFFICIAL_VENUE_PUBLIC_CSV")
