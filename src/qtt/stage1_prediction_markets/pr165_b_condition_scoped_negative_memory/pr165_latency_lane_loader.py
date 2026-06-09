"""Loader for PR165 latency lane rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_latency_lanes(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_LatencyLaneAssignmentRegistry.report.json")


def load_pr165_latency_scores(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_LatencyAdjustedScoreRegistry.report.json")
