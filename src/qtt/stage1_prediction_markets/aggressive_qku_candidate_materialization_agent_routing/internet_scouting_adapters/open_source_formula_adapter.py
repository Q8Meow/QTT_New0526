"""Open-source formula/library scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-OPEN-SOURCE-FORMULA", "TIER_2", "OFFICIAL_OPEN_SOURCE_LIBRARY_DOC")
