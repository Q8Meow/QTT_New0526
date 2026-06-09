"""Test helpers for PR165-B."""

from __future__ import annotations

from pathlib import Path


def repo_root_from_test() -> Path:
    return Path(__file__).resolve().parents[4]
