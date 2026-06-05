"""Test support helpers for PR163."""

from __future__ import annotations

from pathlib import Path

from . import paths as p
from .json_io import read_json, records_from_payload


def load_report(repo_root: Path, filename: str) -> dict:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def load_records(repo_root: Path, filename: str) -> list[dict]:
    return records_from_payload(load_report(repo_root, filename))
