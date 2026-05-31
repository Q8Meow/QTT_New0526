"""PR161A/PR161B foundation loader for PR161E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_discovery import consume_json_report_map


def load_pr161a_reports(repo_root: Path) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for path in sorted((repo_root / c.GENERATED_DIR).glob("PR161A*.report.json")):
        payload = path.read_text(encoding="utf-8", errors="replace")
        reports[path.name] = {"path": path.relative_to(repo_root).as_posix(), "bytes": len(payload)}
    return reports


def load_pr161b_foundation_artifacts(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return consume_json_report_map(repo_root, c.PR161B_REQUIRED_PATHS)
