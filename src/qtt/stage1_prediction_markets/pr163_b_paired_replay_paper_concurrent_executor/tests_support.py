"""Test support helpers for PR163-B reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json
from .report_sharding import load_report_records


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    return load_report_records(repo_root, payload)
