"""Write deterministic PR161E JSON schemas from central constants."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import write_json


def write_schemas(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads = build_schema_payloads()
    for filename, payload in payloads.items():
        write_json(repo_root / c.SCHEMA_DIR / filename, payload)
    return payloads


def build_schema_payloads() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for filename in c.SCHEMA_FILENAMES:
        if filename in {
            "pr161e_replay_result_packet.schema.json",
            "pr161e_paper_result_packet.schema.json",
        }:
            mode = "REPLAY" if "replay" in filename else "PAPER"
            payloads[filename] = _result_packet_schema(filename, mode)
        elif filename == "pr161e_final_summary.schema.json":
            payloads[filename] = _generic_schema(filename, required=("pr_label", "summary_id"))
        else:
            payloads[filename] = _generic_schema(filename)
    return payloads


def _result_packet_schema(filename: str, mode: str) -> dict[str, Any]:
    properties: dict[str, Any] = {
        field: _field_schema(field) for field in c.RESULT_PACKET_REQUIRED_FIELDS
    }
    properties["result_mode"] = {"const": mode}
    properties["result_packet_type"] = {
        "const": f"{mode}_RESULT_PACKET",
        "x-pr161e-enum-source": "RESULT_PACKET_TYPES",
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/{filename}",
        "title": f"{c.PR_LABEL} {mode.title()} Result Packet Candidate Schema",
        "description": (
            "Schema for future validated replay/paper result packets. "
            "Absent values remain pending and cannot create live authority."
        ),
        "type": "object",
        "properties": properties,
        "required": list(c.RESULT_PACKET_REQUIRED_FIELDS),
        "additionalProperties": True,
        "x-pr161e-pr-label": c.PR_LABEL,
        "x-pr161e-schema-enum-source": "src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.constants",
    }


def _generic_schema(filename: str, required: tuple[str, ...] = ("record_id",)) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "record_id": {"type": "string"},
        "pr_label": {"const": c.PR_LABEL},
        "authority_class": {"enum": list(c.AUTHORITY_CLASSES), "x-pr161e-enum-source": "AUTHORITY_CLASSES"},
    }
    for field, values in c.SCHEMA_ENUM_FIELDS.items():
        properties[field] = {"enum": list(values), "x-pr161e-enum-source": field}
    for field in c.TRACEABILITY_FIELDS:
        properties.setdefault(field, {})
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/{filename}",
        "title": f"{c.PR_LABEL} {filename}",
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": True,
        "x-pr161e-pr-label": c.PR_LABEL,
        "x-pr161e-schema-enum-source": "src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.constants",
    }


def _field_schema(field: str) -> dict[str, Any]:
    if field in c.SCHEMA_ENUM_FIELDS:
        return {"enum": list(c.SCHEMA_ENUM_FIELDS[field]), "x-pr161e-enum-source": field}
    if field in c.RESULT_NUMERIC_FIELDS:
        return {"type": ["number", "integer", "null"]}
    if field.endswith("_flag"):
        return {"type": "boolean"}
    if field == "qku_ids":
        return {"type": "array", "items": {"type": "string"}}
    return {"type": ["string", "null", "object", "array", "boolean", "number", "integer"]}
