"""Write deterministic PR162A JSON schemas from central constants."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .json_io import write_json


def write_schemas(repo_root) -> dict[str, dict[str, Any]]:
    payloads = build_schema_payloads()
    for filename, payload in payloads.items():
        write_json(repo_root / c.SCHEMA_DIR / filename, payload)
    return payloads


def build_schema_payloads() -> dict[str, dict[str, Any]]:
    return {
        schema_filename: _generic_report_schema(report_filename, schema_filename)
        for report_filename, schema_filename in zip(
            c.REPORT_FILENAMES,
            c.SCHEMA_FILENAMES,
            strict=True,
        )
    }


def _generic_report_schema(report_filename: str, schema_filename: str) -> dict[str, Any]:
    record_properties: dict[str, Any] = {
        "record_id": {"type": "string"},
        "created_by_pr": {"const": c.PR_ID},
        "authority_class": {"const": c.AUTHORITY_CLASS},
    }
    for field, values in c.SCHEMA_ENUM_FIELDS.items():
        record_properties[field] = {
            "enum": list(values),
            "x-pr162a-enum-source": f"{c.PACKAGE_IMPORT}.constants:{field}",
        }
    report_properties: dict[str, Any] = {
        "report_id": {"type": "string"},
        "report_filename": {"const": report_filename},
        "schema_ref": {"const": c.REPORT_SCHEMA_REFS[report_filename]},
        "created_by_pr": {"const": c.PR_ID},
        "authority_class": {"const": c.AUTHORITY_CLASS},
        "source_inputs": {"type": "array", "items": {"type": "string"}},
        "upstream_pr_refs": {"type": "array", "items": {"type": "string"}},
        "downstream_pr_routes": {"type": "array", "items": {"type": "string"}},
        "validation_status": {"type": "string"},
        "blocker_codes": {"type": "array", "items": {"type": "string"}},
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": record_properties,
                "required": ["record_id"],
                "additionalProperties": True,
            },
        },
        "sharded_flag": {"type": "boolean"},
        "shard_files": {"type": "array", "items": {"type": "string"}},
        **{flag: {"const": value} for flag, value in c.NO_AUTHORITY_FLAGS.items()},
    }
    if report_filename == "PR162A_FinalSummary.report.json":
        report_properties["pr152_currentization_result"] = {
            "enum": list(c.PR152_CURRENTIZATION_RESULTS),
            "x-pr162a-enum-source": f"{c.PACKAGE_IMPORT}.constants:PR152_CURRENTIZATION_RESULTS",
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/{schema_filename}",
        "title": f"{c.PR_ID} {report_filename}",
        "type": "object",
        "properties": report_properties,
        "required": [
            "report_id",
            "report_filename",
            "schema_ref",
            "created_by_pr",
            "authority_class",
            "source_inputs",
            "upstream_pr_refs",
            "downstream_pr_routes",
            "validation_status",
            "blocker_codes",
            "records",
            "sharded_flag",
            *c.NO_AUTHORITY_FLAGS.keys(),
        ],
        "additionalProperties": True,
        "x-pr162a-schema-enum-source": f"{c.PACKAGE_IMPORT}.constants",
    }
