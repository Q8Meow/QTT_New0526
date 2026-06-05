"""Test helpers for PR162R-B reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


def load_report(repo_root: Path, filename: str) -> dict[str, Any]:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    return records_from_payload(load_report(repo_root, filename))


def load_summary(repo_root: Path) -> dict[str, Any]:
    return load_report(repo_root, "PR162R_B_FinalSummary.report.json")
