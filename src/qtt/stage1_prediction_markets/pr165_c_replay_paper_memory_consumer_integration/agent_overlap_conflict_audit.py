"""Agent overlap/conflict audit projection."""

from __future__ import annotations

from .core_tables import build_agent_overlap_conflict_rows, build_core_tables


def build_agent_overlap_conflict_rows_for_repo(repo_root):
    tables = build_core_tables(repo_root)
    return build_agent_overlap_conflict_rows(tables["AgentDutyCoreTable"])
