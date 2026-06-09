"""Loader for the PR165-B negative-memory candidate handoff."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_memory_handoff(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_PR165BNegativeMemoryCandidateHandoff.report.json")
