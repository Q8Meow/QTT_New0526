"""Loader for PR165 global scoring rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_scores(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_GlobalCandidateRanking.report.json")
