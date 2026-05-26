"""PR153 validation entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .report import validate_report, validate_repository_artifacts


def validate(
    report: Mapping[str, Any],
    repo_root: Path | str,
) -> list[str]:
    return validate_report(report, repo_root)


__all__ = ["validate", "validate_report", "validate_repository_artifacts"]
