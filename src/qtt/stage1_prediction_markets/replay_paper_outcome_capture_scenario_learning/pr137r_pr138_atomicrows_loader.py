"""AtomicRows and PR154 compatibility loader for PR161E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_discovery import consume_json_report_map, load_records


def load_atomicrows_contract_artifacts(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return consume_json_report_map(repo_root, c.ATOMICROWS_CONTRACT_PATHS)


def load_atomicrows_pr154_entity_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source_class, path in (
        ("ATOMICROWS", c.PR161C_REPORT_PATHS["atomicrows_bridge"]),
        ("PR154", c.PR161C_REPORT_PATHS["pr154_bridge"]),
    ):
        for record in load_records(repo_root, path):
            merged = dict(record)
            merged["compatibility_source_class"] = source_class
            records.append(merged)
    return records
