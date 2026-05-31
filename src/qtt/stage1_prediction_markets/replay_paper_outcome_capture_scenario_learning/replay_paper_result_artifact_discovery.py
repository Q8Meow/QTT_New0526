"""Public result artifact discovery entry points."""

from __future__ import annotations

from pathlib import Path

from .artifact_discovery import discover_result_like_artifacts


def discover(repo_root: Path) -> list[dict]:
    return discover_result_like_artifacts(repo_root)
