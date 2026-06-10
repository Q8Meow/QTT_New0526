"""Dashboard consumer handoff projection."""

from __future__ import annotations

from .core_tables import build_core_tables, build_dashboard_rows


def build_dashboard_handoff_rows(repo_root):
    return build_dashboard_rows(build_core_tables(repo_root)["MemoryConsumerCoreTable"])
