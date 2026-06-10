"""Test helpers for PR165-D."""

from __future__ import annotations

from pathlib import Path

from .report_builder import build_payloads


def build_test_payloads(repo_root: Path):
    return build_payloads(repo_root)
