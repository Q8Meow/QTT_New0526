"""Write compact permissive schemas for PR162B reports."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    for report_filename, schema_filename in zip(c.REPORT_FILENAMES, c.SCHEMA_FILENAMES, strict=True):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": c.REPORT_SCHEMA_REFS[report_filename],
            "title": report_filename,
            "type": "object",
            "required": [
                "report_id",
                "report_filename",
                "created_by_pr",
                "authority_class",
                "records",
            ],
            "properties": {
                "report_id": {"type": "string"},
                "report_filename": {"const": report_filename},
                "created_by_pr": {"const": c.PR_ID},
                "authority_class": {"const": c.AUTHORITY_CLASS},
                "records": {"type": "array"},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / schema_filename, schema)
