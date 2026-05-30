"""PR136 and roadmap control-plane loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json


def load_control_plane_artifacts(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root)
    payloads: dict[str, Any] = {}
    for key, path in sorted(c.CONTROL_PLANE_PATHS.items()):
        full_path = root / path
        if not full_path.exists():
            continue
        if full_path.suffix.lower() == ".json":
            payloads[key] = read_json(full_path)
        else:
            payloads[key] = {"path": path.as_posix(), "text_length": len(full_path.read_text(encoding="utf-8"))}
    return payloads
