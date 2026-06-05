"""Schema writer for PR162D-R2A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def formulation_record_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FormulationRecordV1",
        "type": "object",
        "required": [
            "formulation_id",
            "formulation_type",
            "domain_family_key",
            "subfamily_key",
            "variant_key",
            "source_universe",
            "source_record_ids",
            "callable_ref",
            "source_truth_status",
            "candidate_truth_status",
            "live_order_authority",
            "replay_paper_candidate_flag",
            "validator_materiality_status",
        ],
        "properties": {
            "formulation_id": {"type": "string"},
            "formulation_type": {"type": "string"},
            "domain_family_key": {"type": "string"},
            "subfamily_key": {"type": "string"},
            "variant_key": {"type": "string"},
            "source_record_ids": {"type": "array"},
            "expression": {"type": ["string", "null"]},
            "algorithm_procedure": {"type": ["string", "null"]},
            "objective": {"type": ["string", "null"]},
            "callable_ref": {"type": "string"},
            "inputs": {"type": "array"},
            "variables": {"type": "array"},
            "outputs": {"type": "array"},
            "objective_output_meaning": {"type": ["string", "null"]},
            "units_or_type_hints": {"type": "object"},
            "unit_unknown_but_type_known_flag": {"type": "boolean"},
            "test_vector_refs": {"type": "array"},
            "live_order_authority": {"const": False},
        },
        "additionalProperties": True,
    }


def candidate_packet_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "CandidatePacketV1",
        "type": "object",
        "required": [
            "candidate_packet_id",
            "source_universe",
            "source_record_ids",
            "domain_family_key",
            "subfamily_key",
            "variant_key",
            "candidate_type",
            "formulation_materialization_state",
            "source_truth_status",
            "candidate_truth_status",
            "official_truth_flag",
            "candidate_or_provisional_flag",
            "replay_paper_candidate_flag",
            "live_order_authority",
            "schema_version",
        ],
        "properties": {
            "candidate_packet_id": {"type": "string"},
            "formulation_ref": {"type": ["string", "null"]},
            "exact_fill_action_ref": {"type": ["string", "null"]},
            "qku_ids": {"type": "array"},
            "callable_ref": {"type": ["string", "null"]},
            "inputs": {"type": "array"},
            "outputs": {"type": "array"},
            "test_vectors": {"type": "array"},
            "live_order_authority": {"const": False},
            "official_truth_flag": {"const": False},
            "schema_version": {"const": "CandidatePacketV1"},
        },
        "anyOf": [
            {"required": ["formulation_ref"]},
            {"required": ["exact_fill_action_ref"]},
        ],
        "additionalProperties": True,
    }


def report_schema(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
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
    }


def write_schemas(repo_root: Path) -> None:
    write_json(repo_root / p.SCHEMA_DIR / p.FORMULATION_RECORD_SCHEMA, formulation_record_schema())
    write_json(repo_root / p.SCHEMA_DIR / p.CANDIDATE_PACKET_SCHEMA, candidate_packet_schema())
    for filename in p.REPORT_FILENAMES:
        schema_filename = filename.replace(".report.json", ".schema.json")
        write_json(repo_root / p.SCHEMA_DIR / schema_filename, report_schema(filename))
