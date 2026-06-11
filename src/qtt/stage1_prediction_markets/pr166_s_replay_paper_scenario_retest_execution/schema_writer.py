"""Schema writer for PR166-S generated reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def _schema(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": [
            "artifact_id",
            "artifact_path",
            "report_id",
            "pr_id",
            "report_filename",
            "created_by_pr",
            "authority_class",
            "validation_status",
            "record_count",
            "upstream_pr_refs",
            "downstream_pr_refs",
            "authority_boundary_ref",
            "no_orphan_status",
        ],
        "properties": {
            "artifact_id": {"type": "string"},
            "artifact_path": {"type": "string"},
            "report_id": {"type": "string"},
            "pr_id": {"const": "PR166-S"},
            "report_filename": {"type": "string"},
            "created_by_pr": {"const": "PR166-S"},
            "authority_class": {"type": "string"},
            "validation_status": {"const": "PASS"},
            "record_count": {"type": "integer", "minimum": 0},
            "records": {"type": "array", "items": {"type": "object"}},
            "shard_files": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }


def write_schemas(repo_root: Path) -> None:
    for filename in p.SCHEMA_FILENAMES:
        write_json(p.schema_path(repo_root, filename), _schema(filename))
