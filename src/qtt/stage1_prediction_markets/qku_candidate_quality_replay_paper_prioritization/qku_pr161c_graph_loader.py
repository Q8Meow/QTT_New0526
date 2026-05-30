"""PR161C orchestration graph loader for PR161D."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_discovery import read_report_records


def load_graph_nodes(repo_root: Path) -> list[dict[str, Any]]:
    return read_report_records(repo_root, c.PR161C_REPORT_PATHS["graph_nodes"])


def load_graph_edges(repo_root: Path) -> list[dict[str, Any]]:
    return read_report_records(repo_root, c.PR161C_REPORT_PATHS["graph_edges"])


def graph_indexes(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    node_by_qku = {str(node["qku_id"]): node for node in nodes if node.get("qku_id")}
    edges_by_qku: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edge_ids_by_qku_type: dict[tuple[str, str], list[str]] = defaultdict(list)
    for edge in edges:
        qku_id = str(edge.get("source_qku_id") or "")
        if not qku_id:
            continue
        edges_by_qku[qku_id].append(edge)
        edge_type = str(edge.get("edge_type") or "")
        edge_ids_by_qku_type[(qku_id, edge_type)].append(str(edge.get("edge_id")))
    return {
        "node_by_qku": node_by_qku,
        "edges_by_qku": dict(edges_by_qku),
        "edge_ids_by_qku_type": dict(edge_ids_by_qku_type),
    }
