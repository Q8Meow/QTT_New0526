"""Commander consumer handoff projection."""

from __future__ import annotations

from .core_tables import build_commander_rows, build_core_tables


def build_commander_handoff_rows(repo_root):
    return build_commander_rows(build_core_tables(repo_root)["PendingRetestCoreTable"])
