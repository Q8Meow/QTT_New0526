"""Scenario memory router projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_scenario_memory_route_rows(repo_root):
    return build_core_tables(repo_root)["ScenarioMemoryRouteCoreTable"]
