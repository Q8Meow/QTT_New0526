"""Test helpers for PR163-C generated reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json
from .report_sharding import load_report_records


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_report(filename: str) -> dict[str, Any]:
    return read_json(repo_root() / p.GENERATED_DIR / filename)


def load_records(filename: str) -> list[dict[str, Any]]:
    return load_report_records(repo_root(), load_report(filename))


def summary() -> dict[str, Any]:
    return load_records("PR163_C_FinalSummary.report.json")[0]
