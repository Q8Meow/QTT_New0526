"""Formula test vector projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_formula_test_vector_rows(repo_root):
    return build_core_tables(repo_root)["FormulaTestVectorCoreTable"]
