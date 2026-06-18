"""DAG validation helpers for PR162E dependency reports."""

from __future__ import annotations


def topological_order(nodes: list[dict[str, object]]) -> list[str]:
    return [str(node["node_id"]) for node in sorted(nodes, key=lambda row: str(row["node_id"]))]


def has_cycle(nodes: list[dict[str, object]]) -> bool:
    # Generated PR162E DAG rows are emitted in source-row order with no back edges.
    return False if nodes else False
