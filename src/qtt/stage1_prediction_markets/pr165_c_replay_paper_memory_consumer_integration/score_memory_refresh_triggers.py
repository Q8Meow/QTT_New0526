"""Score/memory refresh trigger projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_score_memory_refresh_trigger_rows(repo_root):
    return build_core_tables(repo_root)["ScoreMemoryRefreshTriggerCoreTable"]
