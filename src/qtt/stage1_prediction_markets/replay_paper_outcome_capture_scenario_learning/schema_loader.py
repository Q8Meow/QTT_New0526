"""Schema loading helpers for PR161E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json


def load_schema(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / c.SCHEMA_DIR / filename
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"PR161E schema is not an object: {path}")
    return payload


def load_all_schemas(repo_root: Path) -> dict[str, dict[str, Any]]:
    return {filename: load_schema(repo_root, filename) for filename in c.SCHEMA_FILENAMES}
