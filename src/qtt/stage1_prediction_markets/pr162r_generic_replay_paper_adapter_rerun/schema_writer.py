"""Schema writer for PR162R required schema files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json


def _schema(title: str, required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": True,
    }


def replay_paper_adapter_input_schema() -> dict[str, Any]:
    required = [
        "adapter_input_id",
        "candidate_packet_ref",
        "formulation_ref",
        "callable_ref",
        "qku_ids",
        "agent_refs",
        "source_truth_status",
        "candidate_truth_status",
        "replay_paper_candidate_flag",
        "live_order_authority",
        "computability_route",
        "required_inputs",
        "available_inputs",
        "missing_inputs",
        "data_binding_status",
        "fill_action_refs",
        "smoke_execution_status",
        "replay_adapter_status",
        "paper_adapter_status",
        "paired_status",
        "no_result_packet_created",
        "no_live_order_authority",
        "validation_status",
    ]
    return _schema(
        "ReplayPaperAdapterInputV1",
        required,
        {
            "adapter_input_id": {"type": "string"},
            "candidate_packet_ref": {"type": "string"},
            "formulation_ref": {"type": "string"},
            "callable_ref": {"type": "string"},
            "qku_ids": {"type": "array"},
            "agent_refs": {"type": "array"},
            "live_order_authority": {"const": False},
            "no_result_packet_created": {"const": True},
            "no_live_order_authority": {"const": True},
        },
    )


def replay_run_request_schema() -> dict[str, Any]:
    return _schema(
        "ReplayRunRequestCandidateV1",
        ["replay_run_request_candidate_id", "adapter_input_ref", "candidate_packet_ref", "run_request_status"],
        {
            "replay_run_request_candidate_id": {"type": "string"},
            "adapter_input_ref": {"type": "string"},
            "candidate_packet_ref": {"type": "string"},
            "live_order_authority": {"const": False},
        },
    )


def paper_run_request_schema() -> dict[str, Any]:
    return _schema(
        "PaperRunRequestCandidateV1",
        ["paper_run_request_candidate_id", "adapter_input_ref", "candidate_packet_ref", "run_request_status"],
        {
            "paper_run_request_candidate_id": {"type": "string"},
            "adapter_input_ref": {"type": "string"},
            "candidate_packet_ref": {"type": "string"},
            "live_order_authority": {"const": False},
        },
    )


def qku_computability_schema() -> dict[str, Any]:
    return _schema(
        "QKUComputabilityRouteV1",
        ["classification_id", "candidate_packet_ref", "qku_id", "computability_route"],
        {
            "classification_id": {"type": "string"},
            "candidate_packet_ref": {"type": "string"},
            "qku_id": {"type": "string"},
            "computability_route": {"type": "string"},
            "live_order_authority": {"const": False},
        },
    )


def missing_binding_schema() -> dict[str, Any]:
    return _schema(
        "MissingBindingActionV1",
        ["action_id", "candidate_packet_id", "qku_id", "missing_field", "responsible_agent", "priority_score"],
        {
            "action_id": {"type": "string"},
            "candidate_packet_id": {"type": "string"},
            "qku_id": {"type": "string"},
            "priority_score": {"type": "number"},
            "live_order_authority": {"const": False},
        },
    )


def quantum_batch_schema() -> dict[str, Any]:
    return _schema(
        "QuantumBatchPrecomputeRouteV1",
        ["quantum_batch_route_id", "candidate_packet_ref", "formulation_ref", "model_family", "quantum_replay_paper_lane"],
        {
            "quantum_batch_route_id": {"type": "string"},
            "candidate_packet_ref": {"type": "string"},
            "formulation_ref": {"type": "string"},
            "live_order_authority": {"const": False},
        },
    )


def source_candidate_schema() -> dict[str, Any]:
    return _schema(
        "SourceCandidateMaterializationV1",
        ["source_candidate_id", "target_qku_id", "target_field", "source_class", "source_locator", "candidate_truth_status"],
        {
            "source_candidate_id": {"type": "string"},
            "target_qku_id": {"type": "string"},
            "source_class": {"type": "string"},
            "source_locator": {"type": "string"},
            "live_order_authority": {"const": False},
        },
    )


def write_schemas(repo_root: Path) -> None:
    schemas = {
        "ReplayPaperAdapterInputV1.schema.json": replay_paper_adapter_input_schema(),
        "ReplayRunRequestCandidateV1.schema.json": replay_run_request_schema(),
        "PaperRunRequestCandidateV1.schema.json": paper_run_request_schema(),
        "QKUComputabilityRouteV1.schema.json": qku_computability_schema(),
        "MissingBindingActionV1.schema.json": missing_binding_schema(),
        "QuantumBatchPrecomputeRouteV1.schema.json": quantum_batch_schema(),
        "SourceCandidateMaterializationV1.schema.json": source_candidate_schema(),
    }
    for filename, schema in schemas.items():
        write_json(repo_root / p.SCHEMA_DIR / filename, schema)
