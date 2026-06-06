"""Test support helpers for PR163."""

from __future__ import annotations

from pathlib import Path

from . import paths as p
from .json_io import read_json, records_from_payload
from .report_sharding import (
    TRANSITION_REGISTRY_REPORT_FILENAME,
    load_transition_registry_records,
)


def load_report(repo_root: Path, filename: str) -> dict:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def load_records(repo_root: Path, filename: str) -> list[dict]:
    payload = load_report(repo_root, filename)
    if filename == TRANSITION_REGISTRY_REPORT_FILENAME:
        return load_transition_registry_records(repo_root, payload)
    return records_from_payload(payload)
