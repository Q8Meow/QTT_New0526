"""Schema writer for PR162R-A reports."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    for report, schema in zip(c.REPORT_FILENAMES, c.SCHEMA_FILENAMES, strict=True):
        write_json(
            repo_root / c.SCHEMA_DIR / schema,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": report,
                "type": "object",
                "required": [
                    "report_id",
                    "report_filename",
                    "created_by_pr",
                    "authority_class",
                    "validation_status",
                    "record_count",
                    "records",
                ],
                "properties": {
                    "report_id": {"type": "string"},
                    "report_filename": {"type": "string"},
                    "created_by_pr": {"type": "string"},
                    "authority_class": {"type": "string"},
                    "validation_status": {"type": "string"},
                    "record_count": {"type": "integer"},
                    "records": {"type": "array"},
                },
                "additionalProperties": True,
            },
        )
