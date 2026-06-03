"""Social/web signal scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-SOCIAL-WEB-SIGNAL", "TIER_4", "SOCIAL_WEB_RESEARCH_SIGNAL")
