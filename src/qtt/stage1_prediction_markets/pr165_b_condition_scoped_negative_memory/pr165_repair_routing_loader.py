"""Loader for optional PR165 repair route rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_repair_routes(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_RepairRoutingHandoffRegistry.report.json")


def load_pr165_repair_retest_routes(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_RepairRetestRouteRegistry.report.json")
