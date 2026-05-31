"""PR161C QKU inventory and graph loader for PR161E."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .artifact_discovery import load_records, load_report


def load_primary_qkus(repo_root: Path) -> list[dict]:
    return load_records(repo_root, c.PR161C_REPORT_PATHS["master_inventory"])


def load_graph_nodes(repo_root: Path) -> list[dict]:
    return load_records(repo_root, c.PR161C_REPORT_PATHS["graph_nodes"])


def load_graph_edges(repo_root: Path) -> list[dict]:
    return load_records(repo_root, c.PR161C_REPORT_PATHS["graph_edges"])


def load_quantum_forward_records(repo_root: Path) -> list[dict]:
    return load_records(repo_root, c.PR161C_REPORT_PATHS["quantum_forward_inventory"])


def load_range_optimizer_audit(repo_root: Path) -> dict:
    return load_report(repo_root, c.PR161C_REPORT_PATHS["range_optimizer_audit"])


def graph_node_by_qku(graph_nodes: list[dict]) -> dict[str, dict]:
    return {str(record.get("qku_id")): record for record in graph_nodes}
