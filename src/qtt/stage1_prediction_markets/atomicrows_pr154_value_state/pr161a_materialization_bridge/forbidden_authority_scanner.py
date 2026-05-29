"""Forbidden authority scanner for PR161A."""

from __future__ import annotations

from pathlib import Path

from . import constants as c


def forbidden_findings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [pattern for pattern in c.FORBIDDEN_SCAN_PATTERNS if pattern in text]

