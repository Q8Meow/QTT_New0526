"""PR161C QKU inventory loader for PR161D."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .artifact_discovery import read_report, read_report_records


def load_primary_qkus(repo_root: Path) -> list[dict[str, object]]:
    return read_report_records(repo_root, c.PR161C_REPORT_PATHS["master_inventory"])


def load_field_value_facets(repo_root: Path) -> list[dict[str, object]]:
    return read_report_records(repo_root, c.PR161C_REPORT_PATHS["field_facet_linkage"])


def load_pr161c_report(repo_root: Path, key: str) -> dict[str, object]:
    return read_report(repo_root, c.PR161C_REPORT_PATHS[key])
