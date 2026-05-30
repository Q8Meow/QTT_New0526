"""PR161B coverage report loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json


def load_pr161b_coverage_reports(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root)
    return {
        key: read_json(root / path)
        for key, path in sorted(c.PR161B_REPORT_PATHS.items())
        if (root / path).exists()
    }
