"""QKU orchestration graph edge model helpers."""

from __future__ import annotations

from typing import Any

from .qku_id_builder import graph_edge_id


def make_edge(
    *,
    source_qku_id: str,
    edge_direction: str,
    edge_type: str,
    serial: int,
    linked_object_type: str,
    linked_object_id: str,
    linked_object_path: str | None = None,
    linked_object_name: str | None = None,
    linked_pr_label: str | None = None,
    linked_agent_role: str | None = None,
    linked_workflow_stage: str | None = None,
    linked_process_name: str | None = None,
    linkage_basis: str,
    linkage_confidence: str = "HIGH",
) -> dict[str, Any]:
    return {
        "edge_id": graph_edge_id(source_qku_id, edge_direction, edge_type, serial),
        "source_qku_id": source_qku_id,
        "edge_direction": edge_direction,
        "edge_type": edge_type,
        "linked_object_type": linked_object_type,
        "linked_object_id": linked_object_id,
        "linked_object_path": linked_object_path,
        "linked_object_name": linked_object_name,
        "linked_pr_label": linked_pr_label,
        "linked_agent_role": linked_agent_role,
        "linked_workflow_stage": linked_workflow_stage,
        "linked_process_name": linked_process_name,
        "linkage_basis": linkage_basis,
        "linkage_confidence": linkage_confidence,
        "materialized_flag": True,
    }
