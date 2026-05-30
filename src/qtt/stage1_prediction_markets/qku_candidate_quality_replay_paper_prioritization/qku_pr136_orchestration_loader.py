"""PR136 and adjacent control-plane loader for PR161D."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json


def load_control_plane_artifacts(repo_root: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for key, rel_path in c.PR136_CONTROL_PLANE_PATHS.items():
        path = repo_root / rel_path
        if not path.exists() and key == "section_crosswalk_requested":
            path = repo_root / c.PR136_CONTROL_PLANE_PATHS["section_crosswalk_fallback"]
        if not path.exists():
            loaded[key] = {"missing": True, "path": str(rel_path)}
            continue
        if path.suffix.lower() == ".json":
            loaded[key] = read_json(path)
        else:
            loaded[key] = {
                "path": str(rel_path),
                "text_loaded_flag": True,
                "byte_count": path.stat().st_size,
            }
    return loaded
