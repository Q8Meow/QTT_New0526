"""Test helpers for PR162D-R2A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload
from .report_builder import build_payloads


REPO_ROOT = Path(__file__).resolve().parents[4]


def built_payloads() -> dict[str, dict[str, Any]]:
    payloads, _md = build_payloads(REPO_ROOT, p.EXPECTED_BRANCH)
    return payloads


def report(filename: str) -> dict[str, Any]:
    return read_json(REPO_ROOT / p.GENERATED_DIR / filename)


def records(filename: str) -> list[dict[str, Any]]:
    return records_from_payload(report(filename))
