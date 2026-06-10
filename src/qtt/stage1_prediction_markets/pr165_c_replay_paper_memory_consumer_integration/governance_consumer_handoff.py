"""Governance consumer handoff projection."""

from __future__ import annotations

from .core_tables import build_core_tables, build_governance_rows


def build_governance_handoff_rows(repo_root):
    return build_governance_rows(build_core_tables(repo_root)["MemoryConsumerCoreTable"])
