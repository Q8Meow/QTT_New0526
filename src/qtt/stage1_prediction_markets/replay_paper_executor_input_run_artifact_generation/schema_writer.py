"""Write deterministic PR161F JSON schemas from central constants."""

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
    required_by_filename = {
        "pr161f_run_artifact_envelope_record.schema.json": c.RUN_ARTIFACT_REQUIRED_FIELDS,
        "pr161f_synthetic_smoke_run_artifact_record.schema.json": c.RUN_ARTIFACT_REQUIRED_FIELDS,
        "pr161f_real_nonlive_run_artifact_record.schema.json": c.RUN_ARTIFACT_REQUIRED_FIELDS,
        "pr161f_qku_end_to_end_traceability_record.schema.json": c.QKU_TRACEABILITY_REQUIRED_FIELDS,
        "pr161f_agent_workflow_contract.schema.json": c.AGENT_WORKFLOW_REQUIRED_FIELDS,
        "pr161f_agent_role_io_contract.schema.json": c.AGENT_WORKFLOW_REQUIRED_FIELDS,
        "pr161f_agent_communication_protocol.schema.json": ("record_id", "handoff_required_fields", "handoff_states"),
        "pr161f_final_summary.schema.json": ("record_id", "pr_label", "summary_id"),
    }
    for filename in c.SCHEMA_FILENAMES:
        payloads[filename] = _generic_schema(
            filename,
            required=required_by_filename.get(filename, ("record_id",)),
        )
    return payloads


def _generic_schema(filename: str, required: tuple[str, ...]) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "record_id": {"type": "string"},
        "pr_label": {"const": c.PR_LABEL},
        "authority_class": {
            "enum": list(c.AUTHORITY_CLASSES),
            "x-pr161f-enum-source": "AUTHORITY_CLASSES",
        },
    }
    for field, values in c.SCHEMA_ENUM_FIELDS.items():
        properties[field] = {"enum": list(values), "x-pr161f-enum-source": field}
    for field in set(c.RUN_ARTIFACT_REQUIRED_FIELDS + c.QKU_TRACEABILITY_REQUIRED_FIELDS + c.AGENT_WORKFLOW_REQUIRED_FIELDS):
        properties.setdefault(field, _field_schema(field))
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/{filename}",
        "title": f"{c.PR_LABEL} {filename}",
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": True,
        "x-pr161f-pr-label": c.PR_LABEL,
        "x-pr161f-schema-enum-source": c.PACKAGE_IMPORT + ".constants",
    }


def _field_schema(field: str) -> dict[str, Any]:
    if field in c.SCHEMA_ENUM_FIELDS:
        return {"enum": list(c.SCHEMA_ENUM_FIELDS[field]), "x-pr161f-enum-source": field}
    if field.endswith("_flag"):
        return {"type": "boolean"}
    if field.endswith("_roles") or field.endswith("_routes") or field in {"qku_ids", "handoff_states"}:
        return {"type": "array"}
    return {"type": ["string", "null", "object", "array", "boolean", "number", "integer"]}

