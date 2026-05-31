"""PR161E outcome-capture loader for PR161F."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_loaders import consume_json_report_map


def load_pr161e_reports(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return consume_json_report_map(repo_root, c.PR161E_REPORT_PATHS)
