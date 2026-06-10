"""Bounded missing-value materialization projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_bounded_materialization_rows(repo_root):
    return build_core_tables(repo_root)["BoundedMaterializationCoreTable"]
