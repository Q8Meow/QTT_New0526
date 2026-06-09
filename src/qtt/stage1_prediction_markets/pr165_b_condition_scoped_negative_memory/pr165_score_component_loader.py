"""Loader for PR165 score components and score registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_score_components(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_CandidateScoreComponentRegistry.report.json")


def load_score_registry(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    return load_report_records(repo_root, filename)
