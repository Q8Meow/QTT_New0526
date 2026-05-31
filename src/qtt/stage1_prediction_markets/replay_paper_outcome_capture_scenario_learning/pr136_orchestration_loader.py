"""PR136 control-plane loader for PR161E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_discovery import consume_json_report_map


def load_control_plane_artifacts(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return consume_json_report_map(repo_root, c.PR136_CONTROL_PLANE_PATHS)
