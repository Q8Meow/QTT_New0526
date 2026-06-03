"""Quantum formula scouting adapter."""

from __future__ import annotations

from .base import ScoutAdapter


def adapter() -> ScoutAdapter:
    return ScoutAdapter("PR162D-SCOUT-QUANTUM-FORMULA", "TIER_1", "OFFICIAL_QUANTUM_PROVIDER_DOC")
