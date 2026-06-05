"""Test helpers for PR162R generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


def generated_report(repo_root: Path, filename: str) -> dict[str, Any]:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def generated_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    return records_from_payload(generated_report(repo_root, filename))
