"""Retest priority ranking projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_retest_priority_rows(repo_root):
    return build_core_tables(repo_root)["RetestPriorityCoreTable"]
