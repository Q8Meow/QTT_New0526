"""Write PR163-C JSON schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .central_pretrade_repair_reason_codes import ALLOWED_DISPOSITIONS, PROHIBITED_DISPOSITIONS
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    for filename in p.SCHEMA_FILENAMES:
        write_json(repo_root / p.SCHEMA_DIR / filename, _generic_schema(filename))


def _generic_schema(filename: str) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/pr163-c/{filename}",
        "title": filename,
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "validation_status": {"type": "string"},
            "created_by_pr": {"type": "string"},
            "records": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        },
        "pr163_c_allowed_dispositions": sorted(ALLOWED_DISPOSITIONS),
        "pr163_c_prohibited_dispositions": sorted(PROHIBITED_DISPOSITIONS),
    }
    return schema
