"""Model quality challenge projection."""

from __future__ import annotations

from .core_tables import build_core_tables, build_model_quality_challenge_rows


def build_model_quality_challenge_rows_for_repo(repo_root):
    tables = build_core_tables(repo_root)
    return build_model_quality_challenge_rows(tables["AgentDutyCoreTable"])
