"""Orphan audit projection."""

from __future__ import annotations

from .core_tables import build_core_tables, orphan_audit_rows


def build_orphan_audit_rows(repo_root):
    return orphan_audit_rows(build_core_tables(repo_root))
