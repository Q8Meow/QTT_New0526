"""PR136 control-plane loader for PR161F."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_loaders import consume_json_report_map, load_report


def load_pr136_control_plane(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    reports = consume_json_report_map(repo_root, c.PR136_CONTROL_PLANE_PATHS)
    if reports.get("section_crosswalk") is None and (repo_root / c.PR136_CROSSWALK_FALLBACK_PATH).exists():
        reports["section_crosswalk"] = load_report(repo_root, c.PR136_CROSSWALK_FALLBACK_PATH)
        reports["section_crosswalk_fallback_path"] = {
            "path": c.PR136_CROSSWALK_FALLBACK_PATH.as_posix(),
            "reason": "REQUESTED_PR136_CROSSWALK_REPORT_EVOLVED_TO_COVERAGE_TO_READINESS_DOMAIN_MAP",
        }
    return reports

