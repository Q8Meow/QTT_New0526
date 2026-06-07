"""Write PR164 JSON schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .central_reason_codes import as_schema_enum_payload
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    enum_payload = as_schema_enum_payload()
    for filename in p.SCHEMA_FILENAMES:
        schema = _generic_schema(filename, enum_payload)
        write_json(repo_root / p.SCHEMA_DIR / filename, schema)


def _generic_schema(filename: str, enum_payload: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/pr164/{filename}",
        "title": filename,
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "validation_status": {"type": "string"},
            "created_by_pr": {"type": "string"},
            "records": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        },
    }
    if "central_reason_codes" in filename or filename == "central_reason_codes.schema.json":
        schema["properties"]["central_reason_codes"] = {"type": "object"}
        schema["central_reason_codes"] = enum_payload
    return schema
