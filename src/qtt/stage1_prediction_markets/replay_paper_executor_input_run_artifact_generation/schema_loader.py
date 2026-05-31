"""Load PR161F schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json


def load_all_schemas(repo_root: Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for filename in c.SCHEMA_FILENAMES:
        path = repo_root / c.SCHEMA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(path)
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"PR161F schema is not an object: {path}")
        schemas[filename] = payload
    return schemas

