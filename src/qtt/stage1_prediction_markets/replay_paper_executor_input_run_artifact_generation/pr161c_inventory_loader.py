"""PR161C inventory loader for PR161F."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_loaders import load_records


def load_pr161c_inventory(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "qkus": load_records(repo_root, c.PR161C_REPORT_PATHS["master_inventory"]),
        "graph_nodes": load_records(repo_root, c.PR161C_REPORT_PATHS["graph_nodes"]),
        "graph_edges": load_records(repo_root, c.PR161C_REPORT_PATHS["graph_edges"]),
        "quantum_forward": load_records(repo_root, c.PR161C_REPORT_PATHS["quantum_forward_inventory"]),
    }

