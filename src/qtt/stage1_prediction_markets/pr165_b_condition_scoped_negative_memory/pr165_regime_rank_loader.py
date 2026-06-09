"""Loader for PR165 regime-sliced ranking rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_regime_ranks(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_RegimeSlicedRanking.report.json")
