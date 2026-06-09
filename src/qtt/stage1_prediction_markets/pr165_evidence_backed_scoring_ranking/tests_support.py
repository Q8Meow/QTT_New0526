"""Test support helpers for PR165."""

from pathlib import Path

from .report_builder import build_payloads


def build_test_payloads(repo_root: Path):
    return build_payloads(repo_root)
