"""Write compact JSON schemas for PR162R-B generated records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def write_schemas(repo_root: Path) -> None:
    for filename in p.SCHEMA_FILENAMES:
        write_json(p.schema_path(repo_root, filename), _schema(filename))


def _schema(filename: str) -> dict[str, Any]:
    title = filename.replace(".schema.json", "")
    required = {
        "BindingTaskV1.schema.json": ["binding_task_id", "binding_family", "dedup_group_label", "impacted_missing_action_refs"],
        "SourceAcquisitionCandidateV1.schema.json": ["source_candidate_id", "source_class", "source_locator", "candidate_truth_status"],
        "DatasetNormalizationReceiptV1.schema.json": ["normalization_receipt_id", "source_candidate_id", "binding_task_id"],
        "ReplayPaperDatasetBindingV1.schema.json": ["binding_id", "binding_task_id", "binding_family", "binding_status"],
        "RowBindingResolutionV1.schema.json": ["candidate_packet_id", "binding_task_refs", "replay_binding_refs", "paper_binding_refs"],
        "BindingReadinessDeltaV1.schema.json": ["readiness_delta_id", "raw_missing_actions_consumed", "rows_with_any_binding_improvement"],
    }.get(filename, ["binding_id"])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "additionalProperties": True,
        "required": required,
        "properties": {field: {"type": ["string", "array", "number", "integer", "boolean", "object"]} for field in required},
    }
