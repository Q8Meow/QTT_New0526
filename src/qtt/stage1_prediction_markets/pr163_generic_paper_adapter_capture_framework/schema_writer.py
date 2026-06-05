"""Schema writer for PR163 contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def _schema(name: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": name,
        "title": name.replace(".schema.json", ""),
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "candidate_packet_id": {"type": "string"},
            "validation_status": {"const": "PASS"},
            "live_order_authority": {"const": False},
        },
    }


def write_schemas(repo_root: Path) -> None:
    for filename in p.SCHEMA_FILENAMES:
        write_json(p.schema_path(repo_root, filename), _schema(filename))
