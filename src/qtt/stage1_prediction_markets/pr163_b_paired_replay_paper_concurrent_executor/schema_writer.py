"""Schema writer for PR163-B contract artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    for filename in p.SCHEMA_FILENAMES:
        title = filename.removesuffix(".schema.json")
        write_json(p.schema_path(repo_root, filename), _schema(title))


def _schema(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/pr163-b/{title}",
        "title": title,
        "type": "object",
        "required": ["candidate_packet_id", "validation_status"],
        "properties": {
            "candidate_packet_id": {"type": "string"},
            "validation_status": {"type": "string"},
            "no_live_authority": {"type": "boolean"},
            "no_profit_evidence": {"type": "boolean"},
            "no_source_acceptance": {"type": "boolean"},
            "no_connector_binding": {"type": "boolean"},
            "no_private_state_fetch": {"type": "boolean"},
            "no_llm_runtime": {"type": "boolean"},
            "no_quantum_backend": {"type": "boolean"},
        },
        "additionalProperties": True,
    }
