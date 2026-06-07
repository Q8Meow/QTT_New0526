"""Test helpers for PR164 generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json
from .report_sharding import load_report_records


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_report(filename: str, root: Path | None = None) -> dict[str, Any]:
    resolved_root = root or repo_root()
    return read_json(resolved_root / p.GENERATED_DIR / filename)


def load_records(filename: str, root: Path | None = None) -> list[dict[str, Any]]:
    resolved_root = root or repo_root()
    return load_report_records(resolved_root, load_report(filename, resolved_root))


def summary(root: Path | None = None) -> dict[str, Any]:
    return load_records("PR164_FinalSummary.report.json", root)[0]
