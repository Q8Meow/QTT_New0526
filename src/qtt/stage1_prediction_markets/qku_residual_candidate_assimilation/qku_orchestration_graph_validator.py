"""QKU graph validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def validate_graph(records: list[dict[str, Any]], edges: list[dict[str, Any]], repo_root: Path | str) -> list[str]:
    root = Path(repo_root)
    failures: list[str] = []
    edge_ids = [str(edge.get("edge_id")) for edge in edges]
    if len(edge_ids) != len(set(edge_ids)):
        failures.append("QKU_GRAPH_EDGE_ID_DUPLICATE")
    by_qku: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        by_qku.setdefault(str(edge.get("source_qku_id")), []).append(edge)
        if edge.get("edge_type") not in c.QKU_GRAPH_EDGE_TYPES:
            failures.append(f"QKU_GRAPH_EDGE_TYPE_UNKNOWN: {edge.get('edge_type')}")
        path = edge.get("linked_object_path")
        if path and not (root / str(path)).exists():
            failures.append(f"QKU_GRAPH_EDGE_LINKED_PATH_MISSING: {path}")
    for record in records:
        qku_id = str(record.get("qku_id"))
        qku_edges = by_qku.get(qku_id, [])
        up = [edge for edge in qku_edges if edge.get("edge_direction") == "UPSTREAM"]
        down = [edge for edge in qku_edges if edge.get("edge_direction") == "DOWNSTREAM"]
        rejected = record.get("qku_state") in {"QKU_UNSAFE_REJECTED", "QKU_SECRET_REJECTED"}
        if not rejected and not up:
            failures.append(f"QKU_GRAPH_UPSTREAM_EDGE_MISSING: {qku_id}")
        if not rejected and not down:
            failures.append(f"QKU_GRAPH_DOWNSTREAM_EDGE_MISSING: {qku_id}")
        if not rejected and record.get("qku_graph_isolated_flag"):
            failures.append(f"QKU_GRAPH_NON_REJECTED_ISOLATED: {qku_id}")
    return sorted(set(failures))
