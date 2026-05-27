"""Report and artifact writing helpers for PR156."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .builder import build_outputs
from .io import json_dump, write_json_file


def build_registry(repo_root: Path | str) -> dict[str, Any]:
    return dict(build_outputs(repo_root).registry)


def build_report(repo_root: Path | str) -> dict[str, Any]:
    return dict(build_outputs(repo_root).report)


def write_artifacts(repo_root: Path | str) -> tuple[Path, Path]:
    root = Path(repo_root).resolve()
    outputs = build_outputs(root)
    registry_path = root / c.REGISTRY_PATH
    report_path = root / c.REPORT_PATH
    write_json_file(registry_path, outputs.registry)
    write_json_file(report_path, outputs.report)
    return registry_path, report_path


__all__ = ["build_registry", "build_report", "json_dump", "write_artifacts"]
